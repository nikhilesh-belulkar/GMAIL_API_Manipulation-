#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 11 15:49:56 2020 the whackiest year of our lives 

@author: Nikhilesh Belulkar 
This creates an API specific class that logs into the Gmail API and is able to perform specific methods on the gmail API. 
The API is also able to document all new emails and perform operations on the new emails. 
The API is also has a method to create a new label. 

Remember for this to work that we must have have the credentials file loaded in the same folder 

"""

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd 
import base64 
import email 
from apiclient import discovery
from apiclient import errors
from httplib2 import Http
import base64
from bs4 import BeautifulSoup
import re
import time
import dateutil.parser as parser
from datetime import datetime
import datetime
import csv
from apiclient import errors, discovery 
import API_utilities 




SCOPES = ['https://www.googleapis.com/auth/gmail.labels','https://www.googleapis.com/auth/gmail.readonly']

class API(): 
    
    def __init__(self):
        """contains all of the instance variables pertaining to the gmail class that we can use"""
        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        ## If you chnage scopes you have to change the token.pickle delete it and then work from there => token.pickle retains the same scope information
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
    
        self.service = build('gmail', 'v1', credentials=creds)
       


    def GetMessage(self, service, user_id, msg_id): 
          """Get a Message with given ID.
        
          Args:
            service: Authorized Gmail API service instance.
            user_id: User's email address. The special value "me"
            can be used to indicate the authenticated user.
            msg_id: The ID of the Message required.
        
          Returns:
            A dictionary containing key information about the message including the date, sender, subject, message snippet and the full body of the message 
          """
          try:
            message = service.users().messages().get(userId=user_id, id=msg_id).execute()
            temp_dict = parsing_message(message)
            
    
            return temp_dict
        
          except:
            print ('An error occurred') 
        
        
    def ModifyMessage(self, service, user_id, msg_id, msg_labels):
          """Modify the Labels on the given Message.
        
          Args:
            service: Authorized Gmail API service instance.
            user_id: User's email address. The special value "me"
            can be used to indicate the authenticated user.
            msg_id: The id of the message required.
            msg_labels: The change in labels. This is a dictionary that is defined by the following parameters: 
                
                        {
              "addLabelIds": [   ## the new labelId for a message 
                string
              ],
              "removeLabelIds": [ ##the old labelId for the message 
                string
              ]
            }
        
          Returns:
            Modified message, containing updated labelIds, id and threadId.
          """
          try:
            message = service.users().messages().modify(userId=user_id, id=msg_id,
                                                        body=msg_labels).execute()
        
            label_ids = message['labelIds']
        
            print ('Message ID: %s - With Label IDs %s' % (msg_id, label_ids))
            return message
          except:
            print ('An error occurred')
            
            

    def ListMessagesMatchingQuery(self, service, user_id, query=''):
          """List all Messages of the user's mailbox matching the query.
        
          Args:
            service: Authorized Gmail API service instance.
            user_id: User's email address. The special value "me"
            can be used to indicate the authenticated user.
            query: String used to filter messages returned.
            Eg.- 'from:user@some_domain.com' for Messages from a particular sender.
        
          Returns:
            List of Messages that match the criteria of the query. Note that the
            returned list contains Message IDs, you must use get with the
            appropriate ID to get the details of a Message.
          """
          try:
            response = service.users().messages().list(userId=user_id,
                                                       q=query).execute()
            messages = []
            if 'messages' in response:
              messages.extend(response['messages'])
        
            while 'nextPageToken' in response:
              page_token = response['nextPageToken']
              response = service.users().messages().list(userId=user_id, q=query,
                                                 pageToken=page_token).execute()
              messages.extend(response['messages'])
        
            return messages
          except errors.HttpError as error:
            print ('An error occurred: %s' % error)
        

    
    def get_messages_4label(self, label):
        """This method obtains all messages under a particular label, including their bodies, their message ids placing them in a pandas fata frame""" 
        df = pd.DataFrame(columns=["msg_id","thread_id","Sender","Subject","Date","Snippet","Body"])
        
        label_messages = self.ListMessagesMatchingQuery(self.service, user_id="me",query="label:"+label)
        
        
        for msg in label_messages: 
            ID = msg["id"]
            TID =  msg["threadId"]
            msg_info = self.GetMessage(self.service, "me", ID)  #returns the dictionary of all the useful information for a particular message including the parsed text 
          
            #self.service.users().messages().modify(userId="me", id=ID,body={ 'removeLabelIds': ['UNREAD']}).execute()  ##removing the unread label for all the gmail so it can work  
            try:
                new_row = {'msg_id':ID, 'thread_id':TID, 'Sender':msg_info['Sender'],'Subject':msg_info['Subject'],'Date':msg_info['Date'],'Snippet':msg_info['Snippet'],'Body':msg_info['Message_body']}
                df = df.append(new_row, ignore_index=True)
            except: 
                continue 
        return df
    
 



    def get_unread(self): 
        """This method obtains all unread messages including their bodies, their message ids placing them in a pandas data frame that can then be used""" 
        unread_messages = self.ListMessagesMatchingQuery(self.service, user_id="me", query ="is:unread")  ## returns the mesage id and the thread id in a dictionary of all the unread emails 
        
       
            
            
        
        
        df =  pd.DataFrame(columns=["msg_id","thread_id","Sender","Subject","Date","Snippet","Body"])
        
        print("Getting a particular message:")
        
        for unread in unread_messages: 
            ID = unread["id"]
            TID =  unread["threadId"]
            msg_info = self.GetMessage(self.service, "me", ID)  #returns the dictionary of all the useful information for a particular message including the parsed text 
            #self.service.users().messages().modify(userId="me", id=ID,body={ 'removeLabelIds': ['UNREAD']}).execute()  ##removing the unread label for all the gmail so it can work  
            try:
                new_row = {'msg_id':ID, 'thread_id':TID, 'Sender':msg_info['Sender'],'Subject':msg_info['Subject'],'Date':msg_info['Date'],'Snippet':msg_info['Snippet'],'Body':msg_info['Message_body']}
                df = df.append(new_row, ignore_index=True)
            except: 
                continue 
                
          
        
        return df 
    
    
    
    def create_new_label(self, label_name):
        new_label_object = self.MakeLabel(label_name)
        print("EXECUTED AOK ===============>>>>>>>>>>")
        self.CreateLabel(self.service, "me", new_label_object)        
        
    
    def CreateLabel(self, service, user_id, label_object): 
        """Creates a new label within user's mailbox, also prints Label ID.

          Args:
              service: Authorized Gmail API service instance.
              user_id: User's email address. The special value "me"
              can be used to indicate the authenticated user.
              label_object: label to be added.

          Returns:
              Created Label.
              """
        try:
             label = service.users().labels().create(userId=user_id,body=label_object).execute()
             return label
        except errors.HttpError as error:
             print ('An error occurred: %s' % error)
        
    
        
    
    
    
    
    
    
    
    def MakeLabel(self, label_name, mlv='show', llv= 'labelShow'): 
        """Create Label object.

          Args:
              label_name: The name of the Label.
              mlv: Message list visibility, show/hide.
              llv: Label list visibility, labelShow/labelHide.

          Returns:
              Created Label.
              """
        
        label = {'messageListVisibility': mlv,
           'name': label_name,
           'labelListVisibility': llv}
        
        return label




def parsing_message(message): 
    temp_dict = {}
    
    payld = message['payload'] 
    headr = payld['headers'] 

    
    for one in headr: # getting the Subject
     if one['name'] == 'Subject':
         msg_subject = one['value']
         temp_dict['Subject'] = msg_subject
     else:
         pass


    for two in headr: # getting the date
        if two['name'] == 'Date':
            msg_date = two['value']
            date_parse = (parser.parse(msg_date))
            m_date = (date_parse.date())
            temp_dict['Date'] = str(m_date)
        else:
            pass

    for three in headr: # getting the Sender
        if three['name'] == 'From':
            msg_from = three['value']
            temp_dict['Sender'] = msg_from
        else:
            pass
    temp_dict['Snippet'] = message['snippet'] # fetching message snippet
    
    try:
		# Fetching message body
        mssg_parts = payld['parts'] # fetching the message parts
        part_one  = mssg_parts[0] # fetching first element of the part 
        part_body = part_one['body'] # fetching body of the message
        part_data = part_body['data'] # fetching data from the body
        clean_one = part_data.replace("-","+") # decoding from Base64 to UTF-8
        clean_one = clean_one.replace("_","/") # decoding from Base64 to UTF-8
        clean_two = base64.b64decode (bytes(clean_one, 'UTF-8')) # decoding from Base64 to UTF-8
        soup = BeautifulSoup(clean_two , "lxml" )
        mssg_body = soup.body()
		# mssg_body is a readible form of message body
		# depending on the end user's requirements, it can be further cleaned 
		# using regex, beautiful soup, or any other method
        temp_dict['Message_body'] = mssg_body
    
    except :
        temp_dict['Message_body'] = "N/A"
      
    
    return temp_dict # This will create a dictonary item in the final list

	# This will mark the messagea as read
	
   