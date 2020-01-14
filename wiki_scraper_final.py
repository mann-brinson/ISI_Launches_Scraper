#!/usr/bin/env python
# coding: utf-8

# GOAL: Scrape the orbital launches from the wiki site

#Get the html object from wikipedia 
import requests 
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
import pandas as pd

#Get the html object from the web page
url = 'https://en.wikipedia.org/wiki/2019_in_spaceflight#Orbital_launches'
r = requests.get(url, 'html.parser')
soup = BeautifulSoup(r.text, 'html.parser')

#ASSUMPTION: The 'Orbital Launch' table is in the 4th of 29 <tbody> elements
tbody_list = soup.find_all('tbody')
tbody_main = tbody_list[3]

#Compile a list of all <tr> rows
tr_list = tbody_main.find_all('tr')

#GOAL: Read in a list of months from github account
#NOTE: Link active as of 01.13.2020
url = 'https://raw.githubusercontent.com/mann-brinson/ISI_Launches_Scraper/master/months.csv'
months = pd.read_csv(url)
month_list = months['Month'].tolist()

#Try to extract a potential launch date from each <tr> row, using span.strings.
#If the try fails, continue on to the next <tr> row.
list_launchdicts = []
for tr in tr_list:
    try:
        soup_strings = tr.span.strings
    except AttributeError:
        continue
        
    #If a potential launchdate exists from row <tr>, then check if 'launchdate' is not-null.
    launchdate_list = []
    for string in soup_strings:
        launchdate_list.append(string)
    try:
        launchdate = str(launchdate_list[0])
    except IndexError:
        continue
        
    #Next confirm that the <tr> row with launchdate isn't just a month itself (ex: 'January' rather than '10 January').
    #If the <tr> launchdate passes this check, then add to a launch_dict.
    if launchdate not in month_list: #Removes months themselves
        launch_dict = {}
        launch_dict['launchdate'] = launchdate + ' 2019'
        
        #Now, starting from the <tr> row containing launchdate, loop through each row below it, checking for the 'outcome'. 
        # If the outcome is present, append it to a list of dict values. Add these values to the launch_dict.
        # If the outcome is not present, the try statement will fail, and we move onto the initial for loop.
        tr_index_start = tr_list.index(tr)
        tr_counter = 1
        outcome_true_list = []      
        while tr_counter >= 1:
            try:
                td_list = tr_list[tr_index_start + tr_counter].find_all('td') #Gets all cells <td> from the next row to check for 'outcome'
                soup_strings = td_list[5].strings #ASSUMPTION: The 'outcome' is always in the sixth <td> of each <tr>
            except IndexError:
                break
            outcome_list = []
            for string in soup_strings:
                outcome_list.append(string.strip())
            outcome_true = outcome_list[0] #ASSUMPTION: The 'outcome' is always in the first string of the sixth <td>
            outcome_true_list.append(outcome_true)
            launch_dict['outcome'] = outcome_true_list
            tr_counter += 1

        #Add each launch_dict to a list
        list_launchdicts.append(launch_dict)

#Filter out the launches that did not have at least one payload outcome as 'Successful', 'Operational', or 'En Route'.
list_launchdict_successes = []
for launchdict in list_launchdicts:
    if 'Successful' in launchdict['outcome'] or 'Operational' in launchdict['outcome'] or 'En Route' in launchdict['outcome']: 
        list_launchdict_successes.append(launchdict)

#For each successful launch, add to a dictionary
launchcount_dict = {}
for launch in list_launchdict_successes:
    date_time_str = launch['launchdate']
    date_time_obj = datetime.strptime(date_time_str, '%d %B %Y')
    date_time_obj = str(date_time_obj.date())
    if date_time_obj not in launchcount_dict:
        launchcount_dict[date_time_obj] = 1
    else:
        launchcount_dict[date_time_obj] +=1

#Generate a list of dates in 2019
startdate = date(2019, 1, 1)
enddate = date(2019, 12, 31)
delta = enddate - startdate
dates_list = []
for i in range(delta.days + 1):
    day = startdate + timedelta(days=i)
    dates_list.append(str(day))

#Add dates with zero launches to the dictionary
for date in dates_list:
    if date not in launchcount_dict:
        launchcount_dict[date] = 0

# Convert dict into list of tuples, to enable sorting 
list_tuples = [(k, v) for k, v in launchcount_dict.items()]
list_tuples.sort(key=lambda t: datetime.strptime(t[0], '%Y-%m-%d')) #Sort the list of tuples

#Move the tuples into a list of dicts, convert to isoformat
launchcount_list = []
for t in list_tuples:
    launch_dict_final = {}
    
    date_time_str = t[0] #Gets the launch date
    date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d')
    date_time_obj = date_time_obj.isoformat() + "+00:00"
    launch_dict_final['date'] = date_time_obj
    
    value = t[1] #Gets the launch count
    launch_dict_final['value'] = value
    
    launchcount_list.append(launch_dict_final) #Add each launchdate dict to list

#Convert list of dicts to a dataframe
launchcount_df = pd.DataFrame(launchcount_list)
#launchcount_df.head(50)

#Output the df to csv
export_csv = launchcount_df.to_csv ('launch_counts_2019.csv', index = None, header=True)