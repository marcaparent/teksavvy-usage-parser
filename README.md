# TekSavvy Internet Usage Parser

Fetches usage information from TekSavvy's MyWorld interface, and sends them by email. The format is the following:

    Usage_type_display_name: Usage_in_gb

The script is rather straightforward to use:

1. Install Xvfb, pyvirtualdisplay, selenium-python and Firefox (IceWeasel on Linux)
1. Set the correct variables at the top of the script
1. Create the log file and make it writable
1. Mark the script as executable and run it