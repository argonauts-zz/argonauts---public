import os, time, getpass, ConfigParser
from pprint import pprint

class User:
    def __init__(self, key, name, api_key, api_pwd):
        self.Name = name
        self.Key = api_key
        self.Password = api_pwd
        
    def getAuth(self):
        return (self.api_key, self.api_pwd)
        

class APIConfig(object):
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = \
                super(APIConfig, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def getSeries(self):
        series = []
        series.append('Total')
        [series.append(user.Name) for user in self.USERS]
        return series

    def __init__(self):
        self.API_PREFIX = "https://www.toggl.com/api/v6/"
        self.USERS = []
        self.EFFORT_PER_WEEK = 42
        self.NUM_USERS = 5
        
        try:
            home = os.path.expanduser("~")
            togglFile = os.path.join(home, ".toggl")
            config = ConfigParser.RawConfigParser(allow_no_value=True)
            config.read(togglFile)
    
            config_series = {k:v for k,v in config.items("series")}
            config_keys = {k:v for k,v in config.items("api_keys")}
            config_pwds = {k:v for k,v in config.items("api_pwds")}
            
            if len(config_series.keys()) != self.NUM_USERS\
                or len(config_keys.keys()) != self.NUM_USERS\
                or len(config_pwds.keys()) != self.NUM_USERS:
                    print "Invalid Configuration file"
                    return
            
            self.USERS = [User(k,\
                               config_series[k],\
                               config_keys[k],\
                               config_pwds[k]) for k in config_series.keys()]
                
        except ConfigParser.Error:
            print "Error reading ~/.toggl"



