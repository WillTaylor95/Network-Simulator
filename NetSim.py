import random
import os
import sys
import pygame
import Tkinter
import time
from Tkinter import *
from ScrolledText import ScrolledText
from time import sleep
SelectedDevice = None
MouseOverArea = 30
w,h = 800, 500
CableList = []
DeviceList = []
#----------------------------------Classes-------------------------------------

class Interface():
    def __init__(self, name, IP = '0.0.0.0'):
        self.name = name
        self.IP = IP
        self.MACAddress = RandomMAC()

    def Status(self):
        print self.name,self.IP

    def ChangeIP(self, IP):
        self.IP = IP

class Packet():
    def __init__(self):
        self.SourceIP = '0.0.0.0'
        self.DestIP = '0.0.0.0'
        self.SourceMAC = 'AA:AA:AA:AA:AA:AA'
        self.DestMAC = 'AA:AA:AA:AA:AA:AA'
        self.Data = ''

class Device():
    DeviceNo = 0
    def __init__(self,label):
        self.__class__.DeviceNo += 1
        self.InterfaceNo = 0
        self.Interfaces = {}
        self.RoutingTable = {}
        self.ARPTable = {}
        self.Type = label
        self.Label = label + '_' + str(self.__class__.DeviceNo)
        self.PacketInbox = []
        self.PacketOutbox = []
        self.SavedPackets = []
        self.ConnectedDevices = {}
        self.SubnetMask = '255.255.255.0'
        self.Icon = label + 'Icon2.png'
        self.Placement = [w/2,h/2]

    def Send(self, Device, OutPacket):
        Device.Receive(OutPacket)
        self.PacketOutbox.remove(OutPacket)

    def Receive(self,OutPacket):
        self.PacketInbox.append(OutPacket)

    def ListInterfaces(self):
        for interface in self.Interfaces:
            interface.Status()

    def ShowARPTable(self):
        for Entry in self.ARPTable:
            Values = str(Entry) + str(self.ARPTable[Entry]) + '\n'
            Values = 'IP:'+ Values
            Values = Values.replace("'",'')
            Values = Values.replace('{',' ')
            Values = Values.replace('}','')
            Values = Values.replace(': ',':')
            PrintBox.insert(END, Values)

    def ShowRoutingTable(self):
        for route in self.RoutingTable:
            Values = str(route) + str(self.RoutingTable[route])
            Values = Values.replace('Interface','')
            Values = Values.replace('Gateway','')
            Values = Values.replace('  ',' ')
            Values = Values.replace(',','')
            Values = Values.replace('{','')
            Values = Values.replace('}','')
            Values = Values.replace(':','')
            Values = Values.replace("'",'')
            Values = Values.split(' ')
            Info = 'NetworkID:' + Values[0] + ' Interface:' + Values[1] + ' Gateway:' + Values[3]+'\n'
            PrintBox.insert(END, Info)

    def AddRoute(self, NetworkID, interface, gateway):
        self.RoutingTable[NetworkID] = {'Interface':str(interface), 'Gateway':str(gateway)}

    def ChangeIP(self, interface, IP):
        self.Interfaces[interface].ChangeIP(IP)

    def AddInterface(self, name, IP='0.0.0.0'):
        self.Interfaces[name]=(Interface(name,IP))

    def RouteLookup(self, NetworkID):
        return self.RoutingTable[NetworkID]

    def AddToARP(self, MACAddress, IP):
        self.ARPTable[IP] = {'MACAddress':MACAddress}

    def ARPLookup(self, IP):
        MACAddress = self.ARPTable[IP]['MACAddress']
        return MACAddress

    def ShowARP(self):
        for entry in self.ARPTable:
            ARPData = str(entry) + str(self.ARPTable[entry]) + '\n'
            PrintBox.insert(END, ARPData)

class Router(Device):
    def __init__(self):
        Device.__init__(self,'Router')
        self.NoOfConnections = 4

    def ChangeSubnetMask(self, SubnetMask):
        self.SubnetMask = SubnetMask

class Cable():
   def __init__(self):
       self.SP = [0,0]
       self.EP = [0,0]
       self.Colour = [0,0,0]
#--------------------------------------GUI-------------------------------------

def ConvertToNetID(IP, SubnetMask):
    IDCount = 0
    SubnetMask = SubnetMask.split('.')
    IP = IP.split('.')
    NetworkID = ''
    for i in SubnetMask:
        if i == '255':
            IDCount += 1

    for i in range(0, IDCount):
        NetworkID += IP[i]
        NetworkID += '.'

    for i in range(IDCount+1, 5):
        if i != 4:
            NetworkID += '0.'
        else:
            NetworkID += '0'

    print NetworkID
    return NetworkID

def RandomMAC():
   MACL = []
   MACAddress = ''
   a = False
   for i in range(0,12):
       MACL.append (str(random.randint(0,15)))

   for i in range(0,12):
       if MACL[i] == '10':
           MACL[i] = 'A'
       if MACL[i] == '11':
           MACL[i] = 'B'
       if MACL[i] == '12':
           MACL[i] = 'C'
       if MACL[i] == '13':
           MACL[i] = 'D'
       if MACL[i] == '14':
           MACL[i] = 'E'
       if MACL[i] == '15':
           MACL[i] = 'F'

   for i in range(0,12):
       if i % 2 == 0 and i != 0:
           MACAddress += ':'
       MACAddress += str(MACL[i])
   return MACAddress

def Hop():
    for Device in DeviceList:
        for Packet in Device.PacketOutbox:
            Sent = False
            print Device.ConnectedDevices
            for interface in Device.ConnectedDevices:
                if interface.MACAddress == Packet.DestMAC:
                    Device.Send(Device.ConnectedDevices[interface], Packet)
                    PrintBox.insert(END, 'Packet Received at new device \n')
                    Sent = True
            if Sent == False:
                PrintBox.insert(END, 'Packet Lossed \n')
        print Device.PacketOutbox
            

def PacketReconstruction():
    for Device in DeviceList:
        for Packet in Device.PacketInbox:
            for Interface in Device.Interfaces:
                if Packet.DestIP == Device.Interfaces[Interface].IP:
                    Device.SavedPackets.append(Packet)
                    PrintBox.insert(END, 'Successful Ping to ')
                    PrintBox.insert(END, Device.Label + ' \n')
                    Device.PacketInbox.remove(Packet)
                    return

            NetworkID = ConvertToNetID(Packet.DestIP, Device.SubnetMask)
            Route = Device.RouteLookup(NetworkID)
            Packet.SourceMAC = Device.Interfaces[Route['Interface']].MACAddress
            Packet.DestMAC = Device.ARPLookup(Route['Gateway'])
            Device.PacketOutbox.append(Packet)
            Device.PacketInbox.remove(Packet)

def HelpCommand():
   if SelectedDevice.Type == 'Router':
      PrintBox.insert(END, 'help                                 Prints available commands, usage and syntax \n')
      PrintBox.insert(END, 'viewrt                               Shows the routing table for this device \n')
      PrintBox.insert(END, 'addroute [NetID][Interface][Gateway] Adds an entry to the routing table \n')
      PrintBox.insert(END, 'delroute [IP]                        Deletes an entry in the routing table \n')
      PrintBox.insert(END, 'viewarp                              Show this devices ARP table \n')
      PrintBox.insert(END, 'addarp [IP][MACAddress]              Add an entry to the ARP table \n')
      PrintBox.insert(END, 'delarp [IP]                          Deletes a entry from the ARP Table \n')
      PrintBox.insert(END, 'netstatus                            Shows all Interfaces, their MAC and IP \n')


   if SelectedDevice.Type == 'PC':
      PrintBox.insert(END, 'help                                 Prints available commands, usage and syntax \n')
      PrintBox.insert(END, 'ping [Target IP]                     Sends a ping packet to the destination IP \n')
      PrintBox.insert(END, 'viewrt                               Shows the routing table for this device \n')
      PrintBox.insert(END, 'addroute [NetID][Interface][Gateway] Adds an entry to the routing table \n')
      PrintBox.insert(END, 'delroute [IP]                        Deletes an entry in the routing table \n')
      PrintBox.insert(END, 'viewarp                              Show this devices ARP table \n')
      PrintBox.insert(END, 'addarp [IP][MACAddress]              Add an entry to the ARP table \n')
      PrintBox.insert(END, 'delarp [IP]                          Deletes a entry from the ARP Table \n')
      PrintBox.insert(END, 'netstatus                            Shows all Interfaces, their MAC and IP \n')


   if SelectedDevice.Type == 'Server':
      PrintBox.insert(END, 'help                                 Prints available commands, usage and syntax \n')
      PrintBox.insert(END, 'ping [Target IP]                     Sends a ping packet to the destination IP \n')
      PrintBox.insert(END, 'viewrt                               Shows the routing table for this device \n')
      PrintBox.insert(END, 'addroute [NetID][Interface][Gateway] Adds an entry to the routing table \n')
      PrintBox.insert(END, 'delroute [IP]                        Deletes an entry in the routing table \n')
      PrintBox.insert(END, 'viewarp                              Show this devices ARP table \n')
      PrintBox.insert(END, 'addarp [IP][MACAddress]              Add an entry to the ARP table \n')
      PrintBox.insert(END, 'delarp [IP]                          Deletes a entry from the ARP Table \n')
      PrintBox.insert(END, 'netstatus                            Shows all Interfaces, their MAC and IP \n')
      

def netstatusCommand():
    for i in SelectedDevice.Interfaces:
        Entry = 'Name:' + SelectedDevice.Interfaces[i].name + ' '
        Entry += 'IPAddress:' + SelectedDevice.Interfaces[i].IP+ ' '
        Entry += 'MACAddress:'+ SelectedDevice.Interfaces[i].MACAddress + '\n'
        PrintBox.insert(END, Entry)

def viewrtCommand():
    SelectedDevice.ShowRoutingTable()

def viewarpCommand():
    SelectedDevice.ShowARPTable()

def addrouteCommand(NetworkID, Interface, Gateway):
    SelectedDevice.AddRoute(NetworkID, Interface, Gateway)

def addarpCommand(IP, MACAddress):
    SelectedDevice.AddToARP(MACAddress, IP)

def changeipCommand(InterfaceName, NewIP):
    SelectedDevice.Interfaces[InterfaceName].ChangeIP(NewIP)

def delrouteCommand(NetworkID):
    del SelectedDevice.RoutingTable[NetworkID]
           
def delarpCommand(IPAddress):
    del SelectedDevice.ARPTable[IPAddress]

def pingCommand(SourceIP, DestIP, SourceMAC):
    SelectedDevice.PacketOutbox.append(Packet())
    SelectedDevice.PacketOutbox[-1].SourceIP = SourceIP
    SelectedDevice.PacketOutbox[-1].DestIP = DestIP
    SelectedDevice.PacketOutbox[-1].SourceMAC = SourceMAC
    SelectedDevice.PacketOutbox[-1].Data = 'Ping'
    NetworkID = ConvertToNetID(DestIP, SelectedDevice.SubnetMask)
    NextIP = SelectedDevice.RouteLookup(NetworkID)['Gateway']
    SelectedDevice.PacketOutbox[-1].DestMAC = SelectedDevice.ARPLookup(NextIP)
    print SelectedDevice.PacketOutbox[0].SourceIP
    print SelectedDevice.PacketOutbox[0].DestIP
    print SelectedDevice.PacketOutbox[0].SourceMAC
    print SelectedDevice.PacketOutbox[0].DestMAC
    print 'Packet Setup Complete'


#Frame Setup
GUI = Tkinter.Tk()
OuterFrame = Tkinter.Frame(GUI, width = (w+110), height = h)
OuterFrame.grid(columnspan = w, rowspan = h)
GUI.wm_title('NetSim')
GUI.wm_iconbitmap('NetSimLogo2.ico')
Modes = IntVar()

#Widget Setup
def PCBCallback():
   DeviceList.append(Device('PC'))
   Draw()

def RBCallback():
   DeviceList.append(Router())
   Draw()

def SBCallback():
   DeviceList.append(Device('Server'))
   Draw()

def ReturnCommand(event):
   Contents = CommandBox.get()
   CommandBox.delete(0, END)
   CommandBox.insert(END, '$')
   CommandBox.insert(END, SelectedDevice.Label)
   CommandBox.insert(END, '>>> ')
   PrintBox.insert(END,Contents)
   PrintBox.insert(END,'\n')
   RoutingStatus = False
   Recognised = False

   if '>>> help' in Contents:
      HelpCommand()
      Recognised = True

   if '>>> viewrt' in Contents:
      viewrtCommand()
      Recognised = True

   if '>>> ping ' in Contents:
       SplitContents = Contents.split(' ')
       DestIP = SplitContents[2]
       SourceIP = SelectedDevice.Interfaces['eth0'].IP
       SourceMAC = SelectedDevice.Interfaces['eth0'].MACAddress
       pingCommand(SourceIP, DestIP, SourceMAC)
       RoutingStatus = True
       Recognised = True

   if '>>> addarp ' in Contents:
       SplitContents = Contents.split(' ')
       IP = SplitContents[2]
       MACAddress = SplitContents[3]
       addarpCommand(IP, MACAddress)
       PrintBox.insert(END, 'ARP Entry Added \n')
       Recognised = True

   if '>>> viewarp' in Contents:
       viewarpCommand()
       Recognised = True

   if '>>> addroute ' in Contents:
       SplitContents = Contents.split(' ')
       NetworkID = SplitContents[2]
       Interface = SplitContents[3]
       Gateway = SplitContents[4]
       addrouteCommand(NetworkID, Interface, Gateway)
       PrintBox.insert(END, 'Route Added \n')
       Recognised = True

   if '>>> delroute ' in Contents:
       SplitContents = Contents.split(' ')
       NetworkID = SplitContents[2]
       delrouteCommand(NetworkID)
       PrintBox.insert(END, 'Route Deleted \n')
       Recognised = True

   if '>>> delarp ' in Contents:
       SplitContents = Contents.split(' ')
       IPAddress = SplitContents[2]
       delarpCommand(IPAddress)
       PrintBox.insert(END, 'ARP Entry Deleted \n')
       Recognised = True

   if '>>> changeip ' in Contents:
       SplitContents = Contents.split(' ')
       InterfaceName = SplitContents[2]
       NewIP = SplitContents[3]
       changeipCommand(InterfaceName,NewIP)
       PrintBox.insert(END, 'IP of Interface '+InterfaceName+' Changed to '+NewIP+'\n')
       Recognised = True
       
   if '>>> netstatus' in Contents:
       netstatusCommand()
       Recognised = True

   if Recognised == False:
       PrintBox.insert(END, "Command not recognised, type 'help' for a list of commands \n")

   while RoutingStatus == True:
       print RoutingStatus
       for Device in DeviceList:
           print Device.PacketOutbox
           if Device.PacketOutbox != []:
               print 'Hopping'
               Hop()
               PacketReconstruction()
               

           else:
               RoutingStatus = False


def Simulator():
   GUI.update_idletasks()
   
   global SelectedDevice
   mousex, mousey = 0,0
   try:
       Deviceroot = '$' + SelectedDevice.Label + '>>> '

   except:
       Deviceroot = ''
    
   for event in pygame.event.get():
      mousex ,mousey = pygame.mouse.get_pos()

   if pygame.mouse.get_pressed()[0] == 1:
       OuterFrame.focus()
      
   for i in DeviceList:
      if mousex >= i.Placement[0] - MouseOverArea and mousex <= i.Placement[0] + MouseOverArea and mousey >= i.Placement[1] - MouseOverArea and mousey <= i.Placement[1] + MouseOverArea and pygame.mouse.get_pressed()[0] == 1:
         if not SelectedDevice == i:
             SelectedDevice = i
             PrintBox.delete(0.1,END)
             CommandBox.delete(0, END)
             CommandBox.insert(END, Deviceroot)

   Contents = CommandBox.get()
   if not Contents.startswith(Deviceroot):
       CommandBox.delete(0, END)
       CommandBox.insert(END, Deviceroot)
    
def EditMode():
   Got = False
   Selected = []
   mousex, mousey = 0,0
   pressed = 1
   #Draw()

   for event in pygame.event.get():
       mousex ,mousey = pygame.mouse.get_pos()
       
   for i in DeviceList:
      if mousex >= i.Placement[0] - MouseOverArea and mousex <= i.Placement[0] + MouseOverArea and mousey >= i.Placement[1] - MouseOverArea and mousey <= i.Placement[1] + MouseOverArea and pygame.mouse.get_pressed()[0] == 1:
         Selected.append(i)
         Got = True
   if Got == False:
      return

   while pressed == 1:
      for event in pygame.event.get():
         mousex ,mousey = pygame.mouse.get_pos()
         pressed = pygame.mouse.get_pressed()[0]
      Selected[0].Placement[0] = mousex
      Selected[0].Placement[1] = mousey
      Window.fill(pygame.Color(255,255,255))
      Draw()

def CableMode():
   global Con1
   global Con2
   Con1 = []
   Con2 = []
   Dev1 = None
   Dev2 = None
   GotC1 = False
   GotC2 = False
   mousex, mousey = 0,0
   Draw()

   for event in pygame.event.get():
      mousex,mousey = pygame.mouse.get_pos()

   if Dev1 == None:
      for i in DeviceList:
         if mousex >= i.Placement[0] - MouseOverArea and mousex <= i.Placement[0] + MouseOverArea and mousey >= i.Placement[1] - MouseOverArea and mousey <= i.Placement[1] + MouseOverArea and pygame.mouse.get_pressed()[0] == 1:
            Dev1 = i
            Con1.append(i)
            GotC1 = True

   if GotC1 == True:
      while GotC2 == False:
         for event in pygame.event.get():
            mousex, mousey = pygame.mouse.get_pos()

         if Dev1 != None and Dev2 == None:
            for i in DeviceList:
               if mousex >= i.Placement[0] - MouseOverArea and mousex <= i.Placement[0] + MouseOverArea and mousey >= i.Placement[1] - MouseOverArea and mousey <= i.Placement[1] + MouseOverArea and pygame.mouse.get_pressed()[0] == 1:
                  if i != Dev1:
                     Dev2 = i
                     Con2.append(i)
                     GotC2 = True
                  

   if GotC1 == True and GotC2 == True and Con1[0] != Con2[0]:
      CableList.append(Cable())
      CableList[-1].SP = Dev1.Placement
      CableList[-1].EP = Dev2.Placement
      NewInterface1 = 'eth' + str(Con1[0].InterfaceNo)
      NewInterface2 = 'eth' + str(Con2[0].InterfaceNo)
      Con1[0].InterfaceNo += 1
      Con2[0].InterfaceNo += 1
      Con1[0].AddInterface(NewInterface1)
      Con2[0].AddInterface(NewInterface2)
      Con1[0].ConnectedDevices[Con2[0].Interfaces[NewInterface2]] = Con2[0]
      Con2[0].ConnectedDevices[Con1[0].Interfaces[NewInterface1]] = Con1[0]
      GotC1 = False
      GotC2 = False
      Dev1 = None
      Dev2 = None


DevicesLabel = Label(GUI, text = 'New Device:   ')
DevicesLabel.grid(column = 775, row = 25)

ModesLabel = Label(GUI, text = 'Mode:                  ')
ModesLabel.grid(column = 775, row = 75)

PCButton = Button(GUI, text = '        PC        ', command = PCBCallback)
PCButton.grid(column = 775, row = 30)

RouterButton = Button(GUI, text = '     Router     ', command = RBCallback)
RouterButton.grid(column = 775, row = 40)

ServerButton = Button(GUI, text = '     Server      ', command = SBCallback)
ServerButton.grid(column = 775, row = 50)

CableButton = Tkinter.Radiobutton(GUI, text = 'Connections  ', variable = Modes, value = 2)
CableButton.grid (column = 775, row = 80)

EditButton = Tkinter.Radiobutton(GUI, text = 'Device Mover', variable = Modes, value = 1)
EditButton.grid(column = 775, row = 85)

NetworkButton = Tkinter.Radiobutton(GUI, text = 'Simulator       ', variable = Modes, value = 0)
NetworkButton.grid(column = 775, row = 90)

PrintBox = ScrolledText(GUI, width=98, height = 8, pady = 5, state = NORMAL)
PrintBox.grid(column = 0, row = 800)

CommandBox = Tkinter.Entry(GUI, width = 134)
CommandBox.grid(column = 0, row = 805)
CommandBox.bind('<Return>', ReturnCommand)

#Pygame Setup

os.environ['SDL_WINDOWID'] = str(OuterFrame.winfo_id())
#os.environ['SDL_VIDEODRIVER'] = 'windib'
GUI.update()
pygame.init()
pygame.font.init()
Window = pygame.display.set_mode((w+4,h-5))

def DotFix(event):
    if event.y > 20:
        OuterFrame.focus()

OuterFrame.bind("<Button-1>", DotFix)
    

def Draw():
   Window.fill(pygame.Color(255,255,255))
   TagFont = pygame.font.SysFont('Arial', 12)
   for i in CableList:
      pygame.draw.aaline(Window, (0,0,0), (i.SP), (i.EP), 1)
   
   for i in DeviceList:
      Icons = (pygame.image.load(i.Icon))
      IRect = (Icons.get_rect(center = (i.Placement[0], i.Placement[1])))
      Tags = TagFont.render(i.Label,1,(0,0,0))
      TagCoords = [i.Placement[0] - 20, i.Placement[1] + 25]
      Window.blit(Tags, TagCoords)
      Window.blit(Icons, IRect)
   pygame.display.flip()
   OuterFrame.update()

Draw()
Draw()
while 1:
   sleep(0.01)
   #Pygame Activity
   
   Icons = []
   IRect = []

   pygame.display.flip()
   GUI.update()

   if Modes.get() == 1:
      EditMode()
      Draw()
   if Modes.get() == 2:
      CableMode()
      Draw()
   if Modes.get() == 0:
      Simulator()

   


