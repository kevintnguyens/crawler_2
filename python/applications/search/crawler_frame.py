import logging
from datamodel.search.datamodel import ProducedLink, OneUnProcessedGroup, robot_manager
from spacetime_local.IApplication import IApplication
from spacetime_local.declarations import Producer, GetterSetter, Getter
#from lxml import html,etree
import re, os
from time import time,asctime,time
import urlparse
import cgi
from bs4 import BeautifulSoup
from urlparse import urljoin
#final push 2xxx links
try:
    # For python 2
    from urlparse import urlparse, parse_qs
except ImportError:
    # For python 3
    from urllib.parse import urlparse, parse_qs


logger = logging.getLogger(__name__)
LOG_HEADER = "[CRAWLER]"
url_count = (set() 
    if not os.path.exists("successful_urls.txt") else 
    set([line.strip() for line in open("successful_urls.txt").readlines() if line.strip() != ""]))
MAX_LINKS_TO_DOWNLOAD = 3000
subdomains = dict()
mostOutboundLinks = ("url", 0)

@Producer(ProducedLink)
@GetterSetter(OneUnProcessedGroup)
class CrawlerFrame(IApplication):

    def __init__(self, frame):
        self.starttime = time()
        # Set app_id <student_id1>_<student_id2>...
        self.app_id = "13942307_78016851_23968158"
        # Set user agent string to IR W17 UnderGrad <student_id1>, <student_id2> ...
        # If Graduate studetn, change the UnderGrad part to Grad.
        self.UserAgentString ='IR W17 UnderGrad 13942307, 78016851, 23968158'
		
        self.frame = frame
        assert(self.UserAgentString != None)
        assert(self.app_id != "")
        
        self.invalidLinks = 0
        if len(url_count) >= MAX_LINKS_TO_DOWNLOAD:
            self.done = True
        #self.read_file()
    def initialize(self):
        self.count = 0
        l = ProducedLink("http://www.ics.uci.edu", self.UserAgentString)
        print l.full_url
        self.frame.add(l)

    def update(self):
        for g in self.frame.get(OneUnProcessedGroup):
            print "Got a Group"
            outputLinks, urlResps = process_url_group(g, self.UserAgentString)
            for urlResp in urlResps:
                if urlResp.bad_url and self.UserAgentString not in set(urlResp.dataframe_obj.bad_url):
                    urlResp.dataframe_obj.bad_url += [self.UserAgentString]
            for l in outputLinks:
                if is_valid(l) and robot_manager.Allowed(l, self.UserAgentString):
                    lObj = ProducedLink(l, self.UserAgentString)
                    self.frame.add(lObj)
                else:
                    self.invalidLinks+=1
        if len(url_count) >= MAX_LINKS_TO_DOWNLOAD:
            self.done = True
    #look up succsefull urls when the app begins and store the information for use
    #reads fom anayltics overall and url.txt and stores in variable
            #only runs if true
    def read_file(self,overwrite=False):
            if False==overwrite:
                return
            global mostOutboundLinks
            try:
                file_r=open('successful_urls.txt','r')
                for url in file_r:
                    itemSubdomain = (urlparse(url.strip())).hostname
                    itemPath = (urlparse(url.strip())).path

                    if itemSubdomain in subdomains:
                        # subdomain exists

                        if itemPath in subdomains[itemSubdomain]:
                            # path has been crawled, increment count
                            subdomains[itemSubdomain][itemPath] += 1

                        else:
                            subdomains[itemSubdomain][itemPath] = 1
                            
                    else:
                        # subdomain does not exist, create default
                        subdomains[itemSubdomain] = {itemPath: 1}
                #with open("successful_urls.txt", "a") as surls:
                #   surls.write(("\n".join(urls) + "\n").encode("utf-8"))
                file_r.close()
            except Exception as e:
                print e
                pass
            try:
                file_r=open('analytics_overall.txt','r')
                count=0
                
                for line in file_r:
                    x=line.split(':',1)
                    #print(x)
                    if count==0:
                        self.invalidLinks+=int(x[1])
                    if count==1:
                        
                     if x[1] > mostOutboundLinks[1]:
       
                        mostOutboundLinks=(x[1].strip(),1)
                    if count==2  and x[1] > mostOutboundLinks[1]:
      
                        mostOutboundLinks=(mostOutboundLinks[0],int(x[1]))
                    count+=1
                    if count==3:
                        break;
            except Exception as e:
                    print(e)
                    #print(mostOutboundLinks)
                #print(subdomains)
                    pass
            
            #print(mostOutboundLinks)
    def writeAnalyticsToFile(self,file_name='analytics.txt',remove=False):
        try:
            if remove:
                os.remove(file_name)
                
        except:
            pass
        with open(file_name, 'a') as anaFile:
            anaFile.write('Invalid Links: '+str(self.invalidLinks))
            #anaFile.write('\nAverage Download Time: '+str(round((time()-self.starttime), 2)/url_count)+' Seconds')
            anaFile.write('\nPage With Most Outbound Links: '+mostOutboundLinks[0]+' \nwith: '+str(mostOutboundLinks[1])+' \nlinks')
            anaFile.write('\n\nSubdomain Counts:')

            # Print out count of subdomains
            for sub in subdomains:
                subcount = len(subdomains[sub])
                #for path in subdomains[sub]:
                #    subcount += subdomains[sub][path]
                anaFile.write('\n'+str(sub)+': '+str(subcount))
    def shutdown(self):
        print "downloaded ", len(url_count), " in ", time() - self.starttime, " seconds."
        self.writeAnalyticsToFile('analytics'+str(time())+'.txt')
        self.read_file(True)
        self.writeAnalyticsToFile('analytics_overall.txt',True)
        pass

def save_count(urls):
    global url_count
    urls = set(urls).difference(url_count)
    url_count.update(urls)
    if len(urls):
        with open("successful_urls.txt", "a") as surls:
            surls.write(("\n".join(urls) + "\n").encode("utf-8"))

def process_url_group(group, useragentstr):
    rawDatas, successfull_urls = group.download(useragentstr, is_valid)
    save_count(successfull_urls)
    return extract_next_links(rawDatas), rawDatas
    
#######################################################################################
'''
STUB FUNCTIONS TO BE FILLED OUT BY THE STUDENT.
'''
def extract_next_links(rawDatas):
    #most up 2 date
    outputLinks = list()
    #global mostOutboundLinks
    #variables to keep track of information for analytics and is valid
    global mostOutboundLinks
    global subdomains
    '''
    rawDatas is a list of tuples -> [(url1, raw_content1), (url2, raw_content2), ....]
    the return of this function should be a list of urls in their absolute form
    Validation of link via is_valid function is done later (see line 42).
    It is not required to remove duplicates that have already been downloaded. 
    The frontier takes care of that.

    Suggested library: lxml
    '''
    
    #print rawDatas
    #O ( n * k ) k is size of string size
    
    for item in rawDatas:
        tagCount = 0
        #we dont care about the url if redirect. set it as final url
        if(item.final_url != None):
            item.url=item.final_url
        #only grab succesful urls or redirects then we can continue
        if(200<=item.http_code and item.http_code<400):
            #get current url
            current_url=clean_path(item.url)
            soup = BeautifulSoup(item.content, 'lxml')
            #find all url tags from a tags
            for tag in soup.findAll('a',href=True):

                #get the current tag href url
                url=strip_anchor(tag['href'])
                
                
                #url join the path. If the path is absolute it will the taken the second value
                #if it begins with / it replaces the current path
                #if it begins with anything else. it will cleanly join
                
                outputLinks.append(urljoin(current_url,url))

                #keep track of the current the tag amount for current url
                tagCount += 1
            
        # Update for Part 3 in analytics
        if tagCount > mostOutboundLinks[1]:
            mostOutboundLinks = (item.url, tagCount)

        # Track subdomains for analytics
        itemSubdomain = (urlparse(item.url)).hostname
        itemPath = (urlparse(item.url)).path

        if itemSubdomain in subdomains:
            # subdomain exists

            if itemPath in subdomains[itemSubdomain]:
                # path has been crawled, increment count
                subdomains[itemSubdomain][itemPath] += 1

            else:
                subdomains[itemSubdomain][itemPath] = 1
                
        else:
            # subdomain does not exist, create default
            subdomains[itemSubdomain] = {itemPath: 1}
    
    return outputLinks
#given a url. return the query in dictonary
def query_dict(url):
    try:
        url_parse=urlparse(url)
        #found on stackover flow because parse_qs does not work
        return cgi.parse_qs(url_parse.query)
        #return dict(query.split('=') for query in url_parse.query.split("&"))
    except Exception as e:
        print str(e)
        return ''
#given a full base url with htttp etc.. clean it so we can url join  
def clean_path(url):
    parsed=urlparse(url)
    stack=[]
    new_path=''
    for path in parsed.path.split('/'):
        
        if path=='.':
            pass
        elif path=='..' and len(stack)!=0:
            stack.pop()
        else:
            stack.append(path)
    new_path='/'.join(stack)
    query=''
    if parsed.query!='':
        query='?'+parsed.query
    #returns a new built url
    # returns http:://google.com?red=3 http::google.comred=
    return parsed.scheme+'://'+parsed.netloc+new_path+query

#check repeating directory. If a directory path is repeated x amount of times or a string. Its a trap
def check_rep(url, x=3):
    parsed=urlparse(url)
    #get rel path
    rel_path=parsed.path
    path_count=dict()
    #split by path
    for path in rel_path.split('/'):
        if path in path_count:
            path_count[path]+=1
            #prevent from adding relative path
            if (path=='..' or path=='.'):
                return True
            if path_count[path]>x:
                #with open('traps.txt', 'a') as anaFile:
                    #anaFile.write('traps:'+str(parsed.hostname)+str(parsed.path)+'\t Reapeated path\n')
                return True
        else:
            path_count[path]=1
    return False
        
#given a path. Check if it has been visted before

def check_trap(url, x=5):
    #if the url has been visted x amount of times remove it
    parsed=urlparse(url)
    possible_trap=0
    exceptions=['id','ID','page','PAGE','ucinetid']
    querys=query_dict(url)

    #check if file end in php
    if '.php' in url:
        possible_trap=1
    #if there are query values Then its possibly a trap
    if len(querys)!=0:
        possible_trap=1
    
    if possible_trap:
#        return 1
      if parsed.hostname in subdomains:
            # if len is 1. then its a unique identfier
             if len(querys)==1:
                 #check if it is one the found unique identifer
                 for exception in exceptions:
                 
                     if exception in querys:
                         return 0
             if parsed.path in subdomains[parsed.hostname]:
                 if subdomains[parsed.hostname][parsed.path] >= x:
                     #with open('traps.txt', 'a') as anaFile:
                         #anaFile.write('traps:'+str(parsed.hostname)+str(parsed.path)+' Query page was repeated x times\n')

                     return 1
    return 0


def strip_anchor(url):
    return url.split('#')[0]
def is_valid(url):
    '''
    Function returns True or False based on whether the url has to be downloaded or not.
    Robot rules and duplication rules are checked separately.

    This is a great place to filter out crawler traps.
    '''

    url=strip_anchor(url)
    url=clean_path(url)
    parsed = urlparse(url)

    if parsed.scheme not in set(["http", "https"]):
        return False
    if check_trap(url):
        return False
    if check_rep(url):
        return False

    try:
        return ".ics.uci.edu" in parsed.hostname \
            and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4"\
            + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
            + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
            + "|thmx|mso|arff|rtf|jar|csv"\
            + "|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        
        print ("TypeError for ", parsed)
