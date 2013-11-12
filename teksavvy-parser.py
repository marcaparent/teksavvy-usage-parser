#!/usr/bin/env python

from pyvirtualdisplay import Display
from email.MIMEText import MIMEText
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import smtplib
import logging
import MySQLdb as mdb
import time
import sys


# ==============================
# Required account information
# ==============================

USERNAME = '...'  # MyWorld Username
PASSWORD = '...'  # MyWorld Password

# Type of Usage to query
# Note that for DSL connection, TekSavvy doesn't count internet usage from
# 	2AM to 8AM. That's why some date counts in your monthly usage and 
# 	some don't.
# Enter the name you want to be displayed (left) and make sure to let the 
# 	right part as is. Simply delete a line to not send a certain type
USAGE_TYPES = (
	('Download that counts','peakdown'),
	('Upload that counts','peakup'),
	('Total that counts','peaktotal'),
	('Download during the night','offpeakdown'),
	('Upload during the night','offpeakup'),
	('Total during the night','offpeaktotal'),
	('Total download','totaldown'),
	('Total upload','totalup'),
	('Great total','totaltotal'),
)

# SMPT server used to send emails
SMTP_USERNAME = '...'
SMTP_PASSWORD = '...'
SMTP_SERVER = '...'

# Emails infos (sender and receiver)
# You can use SMS gateways to send messages to phones
EMAIL_FROM = '...'
EMAIL_TO = '...'

# MySQL Database Infos
MYSQL_HOST = 'localhost'
MYSQL_USER = '...'
MYSQL_PASSWORD = '...'
MYSQL_DATABASE = 'teksavvy'

# Path to logging file
LOG_PATH = '/var/log/teksavvy-parser-log.txt'


# ==============================
# Prepare the logger
# ==============================

logging.basicConfig(filename=LOG_PATH, level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s')


# ==============================
# Scrape the info from AccesD
# ==============================

# Starting a false graphical interface to open the browser
# Requires pyvirtualdisplay (which requires Xvfb)
display = Display(visible=0, size=(800, 600))
display.start()

logging.info("Scraping usage information from TekSavvy MyWorld")

#Requires IceWeasel
#Set up driver
logging.info("Trying to start driver")
try_number = 1
while try_number > 0: # Had to do this while as my Raspberry Pi sometimes encounter strange errors
	try:
		if try_number > 1:
			try:
				driver.quit() # In case a previous run left traces
			except:
				pass
		driver = webdriver.Firefox()
		logging.info("Driver successfully started")
		try_number = 0
	except:
		logging.warning("Driver error (try " + str(try_number) + "), trying again")
		try_number += 1
driver.implicitly_wait(15)

logging.info("Entering account infos")

#Base will be called more than once
base_adress = "http://myworld.teksavvy.com/"

try:

	#Scrape data
	driver.get(base_adress + "Account/Login.aspx")
	driver.find_element_by_id("MainContent_LoginUser_UserName").clear()
	driver.find_element_by_id("MainContent_LoginUser_UserName").send_keys(USERNAME)
	driver.find_element_by_id("MainContent_LoginUser_Password").clear()
	driver.find_element_by_id("MainContent_LoginUser_Password").send_keys(PASSWORD)
	driver.find_element_by_id("MainContent_LoginUser_LoginButton").click()
	
	logging.info("Accounts infos entered correctly")
	
	driver.find_element_by_link_text("Support").click()
	logging.info("Now trying to switch to Usage page")
	driver.find_element_by_link_text("Check Usage").click()
	logging.info("Sucessfully got to Usage page")

except NoSuchElementException, e:
	logging.error("Could not connect to TekSavvy's website. Failed at login step, page %s. Program will now quit..." % driver.current_url)
	driver.quit()
	display.stop()
	sys.exit(1)

# Fetch the usage list
logging.info("Trying to fetch usage list from " + driver.title)

try:
	usage = {}

	usage['peakdown'] = driver.find_element_by_id("MainContent_PeakDown").text
	usage['peakup'] = driver.find_element_by_id("MainContent_PeakUp").text
	usage['peaktotal'] = driver.find_element_by_id("MainContent_PeakToal").text

	usage['offpeakdown'] = driver.find_element_by_id("MainContent_OffPeakDown").text
	usage['offpeakup'] = driver.find_element_by_id("MainContent_OffPeakUp").text
	usage['offpeaktotal'] = driver.find_element_by_id("MainContent_OffPeakTotal").text

	usage['totaldown'] = driver.find_element_by_id("MainContent_TotalDown").text
	usage['totalup'] = driver.find_element_by_id("MainContent_TotalUp").text
	usage['totaltotal'] = driver.find_element_by_id("MainContent_TotalTotal").text

except NoSuchElementException, e:
	print e
	logging.warning("Couldn't fetch usage list properly")
else:
	logging.info("Accounts fetched successfully")

driver.quit()
display.stop()

# ===========================
# Sabing Usage to Database
# ===========================

logging.info("Trying to save usage to database")

try:
	con = mdb.connect(MYSQL_HOST,MYSQL_USER,MYSQL_PASSWORD,MYSQL_DATABASE)

	cur = con.cursor()
	cur.execute("INSERT INTO ts_usage VALUES(DEFAULT,'%s',%s,%s,%s,%s)" %
		(time.strftime('%Y,%m,%d'),usage['peakdown'],usage['peakup'],usage['offpeakdown'],usage['offpeakup'])) 

	con.commit()
	logging.info("Sucessfully saved usage to database")

except mdb.Error, e:
	if con:
		con.rollback()

	logging.error("Saving to database failed. Error %d: %s" % (e.args[0],e.args[1]))
	sys.exit(1)

finally:
	if con:
		con.close()

# ============================
# Send an SMS with the balance
# ============================

logging.info("Trying to send usage via email to cellphone")

content = "\n"
if len(usage) == 0:
        logging.warning("No accounts found, will send notification anyway")
        content += "Failed to get your accounts balance. Read log in " + LOG_PATH + " for further details"
else:
        for display_name, usage_name in USAGE_TYPES:
		try:
			content += "%s: %s gb\n" % (display_name, usage[usage_name])
		except:
			pass

# Message
message = MIMEText(content, 'plain')
message['From'] = EMAIL_FROM
message['Subject'] = 'Balance'

# Send the email
server = smtplib.SMTP(SMTP_SERVER)
server.ehlo()
server.starttls()
server.ehlo()
server.login(SMTP_USERNAME, SMTP_PASSWORD)
server.sendmail(EMAIL_FROM, EMAIL_TO, message.as_string())
server.quit()

logging.info("Email successfully sent, program will now quit...\n")
