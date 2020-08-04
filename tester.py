#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 11 22:41:26 2020

@author: Nick
"""
from API import API 


ap = API()

#msg =  ap.get_unread()

#print(msg)

print(ap.get_messages_4label("consumer_discretionaries")) 
