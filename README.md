# TekSavvy Internet Usage Parser

- NOT WORKING ANYMORE -
(TekSavvy updated its website and users can now access to detailed infos at myaccount.teksavvy.com, therefore this script won't be supported anymore.)

Fetches usage information from TekSavvy's MyWorld interface, saves them to MySQL Database and sends them by email. 

The email format is the following:

    Usage_type_display_name: Usage_in_gb

The script is rather straightforward to use:

1. Install Xvfb, pyvirtualdisplay, selenium-python and Firefox (IceWeasel on Linux)
1. Import usage.sql to your prefered database
1. Set the correct variables at the top of the script
1. Create the log file and make it writable
1. Mark the script as executable and run it

Upgrade to come: Proper formatting and statistics of MySQL's saved usage info