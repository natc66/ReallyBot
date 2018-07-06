### SENTIMENT ANALYSIS ###
import urllib, urllib2, json
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

#This method converts a string into a text file named chatMsg.txt
#This file will get overwritten for every new message that is analyzed
#Returns the file name as a string
def strToFile(text):
    with open('chatMsg.txt', 'w') as text_file:
        text_file.write(text)
    return 'chatMsg.txt'

#This method looks at polarity and magnitude of a message to determine if it is negative
#The magnitude is divided by the length of the message because magnitude is related to how long the document is.
#Returns True if the message is negative and False otherwise
def review(d):
    msg = open ('chatMsg.txt', 'r')
    msg = msg.read()
    msgList = len(msg.split())
    if d['polarity'] < -0.5:
        if (d['magnitude'])/msgList > .05: 
            return True
    return False

#This method retrieves the sentiment information from the google natural language api
#It uses the strToFile method and review method
#Returns information from the review method
def sentimentApi(text):
    file = strToFile(text)
    credentials = GoogleCredentials.get_application_default()   
    service = discovery.build('language', 'v1', credentials = credentials)
    with open(file, 'r') as msg_file:
        service_request = service.documents().analyzeSentiment(
            body={'document' : {'type' : 'PLAIN_TEXT', 'content' : msg_file.read()}})
        response = service_request.execute()       
    score = response['documentSentiment']['score']
    magnitude = response['documentSentiment']['magnitude']
    d = {'polarity' : score, 'magnitude' : magnitude}
    return review(d)


### TWITCH BOT ###  
import ConfigParser
import socket

s = socket.socket()         #connects to the socket over which to send and receive messages/data
commandList = ['subs_on', 'already_subs_on','subs_off', 'already_subs_off', 'slow_on','slow_off',
               'r9k_on', 'already_r9k_on','r9k_off','already_r9k_off','host_on','bad_host_hosting',
               'host_off','hosts_remaining','emote_only_on', 'already_emote_only_on','already_emote_only_off',
               'msg_channel_suspended','timeout_success','ban_success','unban_success','bad_unban_no_ban',
               'already_banned','unrecognized_cmd']

#takes the message text, determines if it's a message from a user or from the server.
#If it is from a user, it seperates it into the user and message in a dictionary and returns it
#If it is from the server, it sets it up to be printed
def getmsg(text):
    msgList = text.split()
    if msgList[1] == 'PRIVMSG':
        d = {}
        userList = msgList[0].split('!')
        d['user'] = userList[0][1:]
        if len(msgList) > 4:
            usermsg = msgList[3][1:]
            for x in msgList[4:]:
                usermsg = usermsg + ' ' + x
            d['message'] = usermsg
        else:
            d['message'] = msgList[3][1:]
        return d        
    else:
        return 'print'

#Sends a message to the server
def chat(server, msg):
        s.send('PRIVMSG #{} :{} \r\n'.format(server, msg))

#Uses the chat method to ban a user from the channel
def ban(user,server):
    chat(server, ".ban {}".format(user))

#Uses the chat method to timeout a user from the channel   
def timeout(user,server):
    chat(server, ".timeout {}".format(user))

#The bot class. Initializes it by taking the twitch username, oauth key, 
#and the channel they want to join                
class Really:
    #Initializes the bot
    def __init__(self, nick, key, server):
        self.host = "irc.twitch.tv"     #twitch IRC server
        self.port = 6667
        self.nick = nick                #twitch username
        self.auth = key                 #oauth key
        self.server = server         #server to join
        self.dict = {}  
    
    #Runs the bot. Includes ponging teh server, analyzing sentiment, 
    #timingout and banning users, keeping track of the users,
    #and printing the messages to the console
    def run(self):
        s.connect((self.host, self.port))
        s.send("PASS {} \r\n".format(self.auth).encode("utf-8"))
        s.send("NICK {}\r\n".format(self.nick).encode("utf-8"))
        s.send("JOIN #{}\r\n".format(self.server).encode("utf-8"))
       #rate = 0.6666666667             #messages per second

        while True:                    #returns pong when server pings it   
            response = s.recv(1024).decode("utf-8")
            if response == "PING :tmi.twitch.tv\r\n":
                s.send("PONG :tmi.twitch.tv\r\n")
            else:
                d = getmsg(response)
                print d           
                if d == 'print':
                    print response
                else:
                    msg = d['message']
                    user = d['user']
                    for command in commandList:
                        if msg == command:
                            print response
                            d['command'] = True
                        else:
                            d['command'] = False
                    if d['command'] != True:
                        sentiment = sentimentApi(msg)       #True is negative, False is positive/neutral
                        if sentiment == True:
                            if user in self.dict:
                                self.dict[user] += 1
                            else:
                                self.dict[user] = 1
                            print self.dict
                            
                            if self.dict[user] == 5:
                                chat(self.server, user + ' this is your first warning. 2 to go')
                                timeout(user,self.server)
                            if self.dict[user] == 10:
                                chat(self.server, user + ' this is your second warning. 1 to go')
                                timeout(user,self.server) 
                            if self.dict[user] == 15:
                                chat(self.server, user + ' this is your last warning')
                                timeout(user,self.server)                                                               
                            elif self.dict[user] >= 20:
                                ban(user,self.server)
                    

#            else:
#                print(response)
    
        
#code to initialize bot on twitch channel 'hcdenat'             
testNick = ''                              #twitch username
testPass = ''                              #oauth key,
testChannel = ''                            #channel you wish to connect to (should be the same as your username)
test = Really(testNick, testPass, testChannel)
test.run()

#
#
#
#
#
#

