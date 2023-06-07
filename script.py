import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import *
import requests
import urllib.request
import json
import csv
import pandas as pd
from datetime import datetime
import time
from tkcalendar import Calendar, DateEntry
import calendar
from babel.dates import format_date, parse_date, get_day_names, get_month_names
import babel.numbers
import threading

#search date
search_date = time.strftime("%Y-%m-%d")

#drop-down
OPTIONS = [
"https://direct.broadsign.com/",
"https://prod-sandbox-direct.broadsign.com/"
] 

headers = "test"
playout = "test"
df = []
pli_df = []

def start_program():
    start_date = datetime.date(datetime.strptime(date_ent.get(), "%m/%d/%y"))
    end_date = datetime.date(datetime.strptime(date_ent2.get(), "%m/%d/%y"))
    if start_date > end_date:
        run_output.config(text = "Start date is grater then end date")
    else:
        t = threading.Thread(target = script)
        t.start()


def login_bsd():
    #loing to bsd
    global headers
    loginpage = env.get()+"login"
    credentials={
    "email": [str(email.get())],
    "password": [str(password.get())]
    }
    login = requests.request("POST", url=loginpage, headers={}, data=credentials, files=[])
    if str(login) == "<Response [200]>":
        login_out_string.set("Logged")
        token="session="+login.cookies["session"]
        headers={"Cookie": token}
        print(login.cookies['session'])
        print(headers)
        headers = {"Content-Type":"application/json","Cookie": token}
        run_btn["state"] = "normal"
    elif str(login) != "<Response [200]>":
        login_out_string.set("Login Failed. Please check your credentials")
        run_btn["state"] = "disabled"

        
        #script_frame
def script():
    global headers
    global run_btn
    global email
    global password
    global date_ent
    global date_ent2
    global run_output
    global env
    global df
    global search_date
    global pli_df
    global playout
    run_btn.config(text='WORK IN PROGRESS')
    run_output.config(text = "Starting...")
    start_date = datetime.date(datetime.strptime(date_ent.get(), "%m/%d/%y"))
    end_date = datetime.date(datetime.strptime(date_ent2.get(), "%m/%d/%y"))
    #loing to bsd
    login_bsd()
    # Getting the current date and time
    dt = str(datetime.now())
    #add start time to the log file
    start_log = "*******Started at: "+dt
    with open("log.txt","a") as file:
            file.write(start_log)
            file.write("\n")
    search_url = env.get()+"api/v1/proposal/search"
    search_pl = json.dumps({
  "$top": 10000,
  "$skip": 0,
  "$sort": [
    {
      "field": "last_modification_date_time",
      "dir": "desc"
    }
  ],
  "status": ["live", "submitted", "booked"],
  "keyword": "",
  "only_user": False,
  "date": str(search_date)
})
    search = requests.request("POST", url=search_url, headers=headers, data=search_pl)
    df = pd.DataFrame.from_dict(search.json()["data"])
    for index in range(0, len(df)):
        proposal_id = df.iloc[index]["id"]
        proposal_name = df.iloc[index]["name"]
        proposal_start = df.iloc[index]["start_date"]
        proposal_end = df.iloc[index]["end_date"]
        proposal_status = df.iloc[index]["status"]
        proposal_start_dt = datetime.date(datetime.strptime(proposal_start, "%Y-%m-%d"))
        proposal_end_dt = datetime.date(datetime.strptime(proposal_end, "%Y-%m-%d"))
        if proposal_status == 11 and start_date >= proposal_end_dt:
            print("skip "+ str(proposal_id), str(proposal_status), str(proposal_end_dt))
        elif start_date <= proposal_start_dt and end_date >= proposal_start_dt or proposal_status == 11 and start_date >= proposal_start_dt or proposal_status == 14 and start_date <= proposal_end_dt and end_date >= proposal_end_dt:
            #print(proposal_id, proposal_name)
            pli_url = env.get()+"api/v1/proposal/"+str(proposal_id)+"/proposal_items"
            pli = requests.request("POST", url=pli_url, headers=headers, data=[])
            pli_df = pd.DataFrame.from_dict(pli.json()["data"])
            for index2 in range(0, len(pli_df)):
                mode_df = pd.DataFrame.from_dict(pli_df.iloc[index2]["mode"])
                tob_df = mode_df[mode_df["active"]!=False]
                pli_tob_values = tob_df.iloc[0]["values"]
                pli_type = tob_df.iloc[0]["type"]
                pli_id = pli_df.iloc[index2]["id"]
                pli_name = pli_df.iloc[index2]["name"]
                pli_tob = pli_df.iloc[index2]["active_type"]
                pli_cr_tm = pli_df.iloc[index2]["creation_tm"]
                pli_act_imp = pli_df.iloc[index2]["actual_impressions"]
                pli_act_rep = pli_df.iloc[index2]["actual_repetitions"]
                pli_target = pli_df.iloc[index2]["target"]
                pli_status_id = pli_df.iloc[index2]["status"]
                pli_start_dt = pli_df.iloc[index2]["start_date"]
                pli_end_dt = pli_df.iloc[index2]["end_date"]
                pli_end =  datetime.date(datetime.strptime(pli_end_dt, "%Y-%m-%d"))
                pli_start_tm = pli_df.iloc[index2]["start_time"]
                pli_end_tm = pli_df.iloc[index2]["end_time"]
                if pli_status_id == 1:
                     print("Skip "+pli_name+" "+str(pli_status_id))
                elif pli_status_id == 12:
                     print("Skip "+pli_name+" "+str(pli_status_id))
                elif pli_status_id == 14:
                     print("Skip "+pli_name+" "+str(pli_status_id))
                elif pli_status_id == 4:
                    print("Skip "+pli_name+" "+str(pli_status_id))
                #PRocess only Booked, Submitted or Live campaigns
                elif pli_status_id != 1 and pli_status_id != 12 and pli_status_id != 4 and pli_status_id !=14:
                    #Process Repetition TOB
                    if pli_tob == "goal_repetitions":
                        print(pli_name+" Reps "+pli_tob+" "+str(pli_status_id))
                        # Getting the current date and time
                        dt = str(datetime.now())
                        log_data = dt+" Start processing pli ID "+pli_name, str(pli_id)
                        with open("log.txt","a") as file:
                            file.write(str(log_data))
                            file.write("\n")
                            
                        #download playout plan before processing
                        playout_url = env.get()+"api/v1/proposal/proposal_item/"+str(pli_id)+"/playout/csv"


                        playout = requests.request("GET", url = playout_url, headers=headers, data=[])
                        file_name = "playout_plan_"+str(pli_id)+"_before_processing.csv" 
                        ## Write API Results to CSV
                        with open(file_name, "wb") as csvFile:
                            #writer = csv.writer(csvFile, delimiter=',')
                            csvFile.write(bytes(playout.text.encode()))
                        
                        #pull list of screens
                        pli_full_url = env.get()+"api/v1/proposal/proposal_item/"+str(pli_id)+"?include_screens=true"
                        pli_full = requests.request("GET", url=pli_full_url, headers=headers, data=[])
                        pli_screens = pli_full.json()["screens"]
                         # Getting the current date and time
                        dt = str(datetime.now())
                        log_data = dt+" Playout plan has been created for pli "+str(pli_id)+" Amand availibility check starting now"
                        with open("log.txt","a") as file:
                            file.write(str(log_data))
                            file.write("\n")
                         #amend availibility check
                        amend_avil_url = env.get()+"api/v1/proposal/proposal_item/"+str(pli_id)+"/amend/availability"
                        amend_avil_body =  json.dumps({
  "start_date": pli_start_dt,
  "end_date": pli_end_dt,
  "screen_ids": pli_screens,
  "name": pli_name,
  "custom_price": None
})
                        print(amend_avil_body)
                        
                        amend_avil = requests.request("POST", url= amend_avil_url, headers=headers, data=amend_avil_body)
                        print(amend_avil.text) 
                        print(amend_avil_url)
                        
                        #if availible check is ok then amend
                        if amend_avil.json()[ "availability"] == "available":
                            # Getting the current date and time
                            dt = str(datetime.now())
                            log_data = dt+" Availibility check has been finished. PLI ID "+str(pli_id)+" started amending process"
                            with open("log.txt","a") as file:
                                file.write(str(log_data))
                                file.write("\n")
                            amend_url = env.get()+"api/v1/proposal/proposal_item/"+str(pli_id)+"/amend"
                            print(amend_url)
                            
                            amend_body = json.dumps({
  "start_date": pli_start_dt,
  "end_date": pli_end_dt,
  "screen_ids": pli_screens,
  "name": pli_name,
  "custom_price": None
})
                            amend = requests.request("POST", url= amend_url, headers=headers, data=amend_body)
                            
                            #Download palyout plan after processing
                            playout = requests.request("GET", url = playout_url, headers=headers, data=[])
                            file_name = "playout_plan_"+str(pli_id)+"_after_processing.csv" 
                            ## Write API Results to CSV
                            with open(file_name, "wb") as csvFile:
                                #writer = csv.writer(csvFile, delimiter=',')
                                csvFile.write(bytes(playout.text.encode()))
                            
                            # Getting the current date and time
                            dt = str(datetime.now())
                            log_data = dt+" Amend process has finished for PLI ID "+str(pli_id)+" Play out plan has been downloaded."
                            with open("log.txt","a") as file:
                                file.write(str(log_data))
                                file.write("\n")
                                
                        #if availible check is not ok log that to the file
                        else:
                            # Getting the current date and time
                            dt = str(datetime.now())
                            log_data = dt+" Availibility check returned "+ amend_avil.json()[ "availability"]+ "for PLI ID "+str(pli_id)
                            with open("log.txt","a") as file:
                                file.write(str(log_data))
                                file.write("\n")
                        
                        
                        
                        
                    # Process IMP TOB    
                    elif pli_tob == "goal_impressions":  #process imppression campaign
                        print(pli_name+" IMP "+pli_tob+" "+str(pli_status_id))
                         # Getting the current date and time
                        dt = str(datetime.now())
                        log_data = dt+" Start processing pli ID "+pli_name, str(pli_id)
                        with open("log.txt","a") as file:
                            file.write(str(log_data))
                            file.write("\n")
                            
                        #download playout plan before processing
                        playout_url = env.get()+"api/v1/proposal/proposal_item/"+str(pli_id)+"/playout/csv"


                        playout = requests.request("GET", url = playout_url, headers=headers, data=[])
                        file_name = "playout_plan_"+str(pli_id)+"_before_processing.csv" 
                        ## Write API Results to CSV
                        with open(file_name, "wb") as csvFile:
                            #writer = csv.writer(csvFile, delimiter=',')
                            csvFile.write(bytes(playout.text.encode()))
                        
                        #pull list of screens
                        pli_full_url = env.get()+"api/v1/proposal/proposal_item/"+str(pli_id)+"?include_screens=true"
                        pli_full = requests.request("GET", url=pli_full_url, headers=headers, data=[])
                        pli_screens = pli_full.json()["screens"]
                        try:
                            pli_tob_values["goal_impressions_upper_boundary"]
                        except NameError:
                            pli_imp_boundary = None
                        except KeyError:
                            pli_imp_boundary = None
                        else:
                            pli_imp_boundary = pli_tob_values["goal_impressions_upper_boundary"]
                         # Getting the current date and time
                        dt = str(datetime.now())
                        log_data = dt+" Playout plan has beed created for pli "+str(pli_id)+" Amand availibility check starting now"
                        with open("log.txt","a") as file:
                            file.write(str(log_data))
                            file.write("\n")
                         #amend availibility check
                        amend_avil_url = env.get()+"api/v1/proposal/proposal_item/"+str(pli_id)+"/amend/availability"
                        amend_avil_body =  json.dumps({
  "start_date": pli_start_dt,
  "end_date": pli_end_dt,
  "limiter_upper_boundary": pli_imp_boundary,
  "screen_ids": pli_screens,
  "name": pli_name,
  "custom_price": None
})
                        print(amend_avil_body)
                        
                        amend_avil = requests.request("POST", url= amend_avil_url, headers=headers, data=amend_avil_body)
                        print(amend_avil.text) 
                        print(amend_avil_url)
                        
                        #if availible check is ok then amend
                        if amend_avil.json()[ "availability"] == "available":
                            # Getting the current date and time
                            dt = str(datetime.now())
                            log_data = dt+" Availibility check has been finished. PLI ID "+str(pli_id)+" started amending process"
                            with open("log.txt","a") as file:
                                file.write(str(log_data))
                                file.write("\n")
                            amend_url = env.get()+"api/v1/proposal/proposal_item/"+str(pli_id)+"/amend"
                            print(amend_url)
                            
                            amend_body = json.dumps({
  "start_date": pli_start_dt,
  "end_date": pli_end_dt,
  "limiter_upper_boundary": pli_imp_boundary,
  "screen_ids": pli_screens,
  "name": pli_name,
  "custom_price": None
})
                            amend = requests.request("POST", url= amend_url, headers=headers, data=amend_body)
                            
                            #Download palyout plan after processing
                            playout = requests.request("GET", url = playout_url, headers=headers, data=[])
                            file_name = "playout_plan_"+str(pli_id)+"_after_processing.csv" 
                            ## Write API Results to CSV
                            with open(file_name, "wb") as csvFile:
                                #writer = csv.writer(csvFile, delimiter=',')
                                csvFile.write(bytes(playout.text.encode()))
                            
                            # Getting the current date and time
                            dt = str(datetime.now())
                            log_data = dt+" Amend process has finished for PLI ID "+str(pli_id)+" Play out plan has been downloaded."
                            with open("log.txt","a") as file:
                                file.write(str(log_data))
                                file.write("\n")
                                
                        #if availible check is not ok log that to the file
                        else:
                            # Getting the current date and time
                            dt = str(datetime.now())
                            log_data = dt+" Availibility check returned "+ amend_avil.json()[ "availability"]+ "for PLI ID "+str(pli_id)
                            with open("log.txt","a") as file:
                                file.write(str(log_data))
                                file.write("\n")
                            
                        
                                            
                    
                        
                              
    run_btn.config(text='RUN')
    run_output.config(text = "Script has finished")
    print("The end!")
    # Getting the current date and time
    dt = str(datetime.now())
    #add end time to the log file
    start_log = "*******SENDED At : "+dt
    with open("log.txt","a") as file:
            file.write(start_log)
            file.write("\n") 
    





window = tk.Tk()
window.geometry('1200x900')
#title
title_label = ttk.Label(master = window, text = 'Even distro script', font = 'Calibri 24 bold') 
title_label.pack()
#drop-down
Label(window, text = "Choose an env.", background= 'gray61', foreground="white").pack(padx=20,pady=20)
env = StringVar(window)
env.set(OPTIONS[0]) # default value

w = OptionMenu(window, env, *OPTIONS)
w.pack()
#credentials
credential_frame = ttk.Frame(master = window)
email = tk.StringVar()
password = tk.StringVar()
Label(credential_frame, text= "BSD Credentials", background= 'gray61', foreground="white").pack(padx=20,pady=20)
entry_login = ttk.Entry(master = credential_frame, textvariable = email)
entry_password = ttk.Entry(master = credential_frame, show="*", textvariable = password)
login_btn = ttk.Button(master = credential_frame, text = 'LOGIN TO BSD', command = login_bsd)
entry_login.pack(side = 'left')
entry_password.pack(side = 'left')
login_btn.pack(side = 'right')
credential_frame.pack(pady = 10)
#login output
login_out_string = tk.StringVar()
login_out_label = ttk.Label(master = window, text = '', font = 'Calibri 16', textvariable = login_out_string)
login_out_label.pack(pady = 10)
#Create a Label
Label(window, text= "Choose a Date form", background= 'gray61', foreground="white").pack(padx=20,pady=20)
#Create a Calendar using DateEntry
date_ent = tk.StringVar()
cal = DateEntry(window, width= 16, background= "magenta3", foreground= "white",bd=2, textvariable = date_ent)
cal.pack(pady=20)
Label(window, text= "Choose a Date till", background= 'gray61', foreground="white").pack(padx=20,pady=20)
#Create a Calendar using DateEntry
date_ent2 = tk.StringVar()
cal = DateEntry(window, width= 16, background= "magenta3", foreground= "white",bd=2, textvariable = date_ent2)
cal.pack(pady=20)
script_frame = tk.Frame(master = window)
run_btn = tk.Button(master = script_frame, text = 'RUN', width=20, state = DISABLED, command = lambda:start_program())

run_output = ttk.Label(master = script_frame,text='')
script_frame.pack(pady=10)
run_btn.pack()
run_output.pack()
window.mainloop()
