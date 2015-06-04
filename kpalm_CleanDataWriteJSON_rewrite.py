import xml.etree.ElementTree as ET
import re
import codecs
import json

#File location
datafile = r'/home/kevin/Documents/projects/Udacity/Project_2/humboldt_bay_area'

#Define references for street_clean()
streetname = {'Harrison': 'Harrison Avenue', 'Nw Cnr Elk River Int': 'Pound Road', 'Ne Cnr Trinidad Int': 'Trinidad Frontage Road',
              'Nw Cnr Trinidad Int': 'Patricks Point Drive', 'Harris': 'Harris Street', 'Alliance': 'Alliance Road',
              'Se Cnr Kenmar Road Int': 'Kenmar Road', '1924 Smith Lane': 'Smith Lane', 'Hwy 299 PM 12.4':'Highway 299',
              'Broadway': 'Highway 101', 'Myrtle': 'Myrtle Avenue', '1835 6TH Street': '6th Street', '6100 No Hwy 101': 'Highway 101',
              '1656 Union Street': 'Union Street', 'Broadway Street': 'Highway 101'}
fixname = {'St': 'Street'}

#Corrections for addr:street values
def street_clean(street):
    #Fix values which are not actually street names
    if street in streetname.keys():
        street = streetname[street]
    #Fix abbreviations
    words = street.strip().split(' ')
    for word in words:
        if word in fixname.keys():
            street = street.replace(word, fixname[word])
    return street

#Check for and collect root level values
def get_root_values(element):
    node = {}
    if 'id' in element.attrib.keys():
        node['id'] = element.attrib['id']
    node['type'] = element.tag
    if 'visible' in element.attrib.keys():
        node['visible'] = element.attrib['visible']
    if 'lat' in element.attrib.keys() and 'lon' in element.attrib.keys():
        node['pos'] = [float(element.attrib['lat']), float(element.attrib['lon'])]
    #create dictionary for nested 'created' values, try to fill dictionary
    created = {}
    if 'version' in element.attrib.keys():
        created['version'] = element.attrib['version']
    if 'changeset' in element.attrib.keys():
        created['changeset'] = element.attrib['changeset']
    if 'timestamp' in element.attrib.keys():
        created['timestamp'] = element.attrib['timestamp']
    if 'user' in element.attrib.keys():
        created['user'] = element.attrib['user']
    if 'uid' in element.attrib.keys():
        created['uid'] = element.attrib['uid']
    #Nest 'created' dictionary if values found
    if len(created) > 0:
        node['created'] = created
    return node

#References for shape_element() and process_tag()
nesttags = ['addr','name', 'gnis', 'tiger', 'alt_name', 'caltrans', 'nhd', 'county', 'FG', 'csp', 'ref', 'flag',
            'old_name', 'fuel', 'toilets', 'monitoring', 'oneway', 'lanes', 'turn', 'park', 'contact', 'hgv', 'diet',
            'boundary', 'payment', 'census', 'nist', 'internet_access']

#Gather tag keys and values, incorporate instructions for nesting and corrections
def process_tags(element):
    for item in element.iter('tag'):
    #skip tags with problem chars or multiple colons
        if re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]').search(item.attrib['k']) or re.compile(r'[:].+[:]').search(item.attrib['k']):
            continue
        elif item.attrib['k'].find(':') != -1:
            if item.attrib['k'][:item.attrib['k'].find(':')] in nesttags:
                field = item.attrib['k'][:item.attrib['k'].find(':')]
                subfield = item.attrib['k'][item.attrib['k'].find(':') + 1:]
                if item.attrib['k'] == 'addr:state':        #Capitalize state (e.g. 'Ca' to 'CA')
                    nests[field][subfield] = item.attrib['v'].upper()
                elif item.attrib['k'] == 'addr:street':     #Fix street abbreviations and correct values
                    nests[field][subfield] = street_clean(item.attrib['v'])
                elif item.attrib['k'] == 'addr:city':       #Format city names
                    if 'Arcata' in item.attrib['v']:
                        city = 'Arcata'
                    elif 'Fortuna' in item.attrib['v']:
                        city = 'Fortuna'
                    elif 'Trinidad' in item.attrib['v']:
                        city = 'Trinidad'
                    else:
                        city = item.attrib['v']
                    nests[field][subfield] = city
                elif item.attrib['k'] == 'is_in:state':       #Correct state abbreviations
                    if item.attrib['v'] == 'California':
                        nests[field][subfield] = 'CA'
                    else:
                        nests[field][subfield] = item.attrib['v']
                else:                                       #add any other 'address' values as they are
                    nests[field][subfield] = item.attrib['v']
        #Fix values in specific tag fields
        elif item.attrib['k'] == 'type':    #Lowercase type (e.g. 'Public' to 'public')
            node[item.attrib['k']] = item.attrib['v'].lower()
        elif item.attrib['k'] == 'fax' or item.attrib['k'] == 'phone':
            numbers = item.attrib['v'].strip().replace(' ', '').replace('.', '').replace('-', '').replace('(', '').replace(')', '')[-10:]
            try:    #If numbers (actual phone number rather than 'Yes' or 'No' value), convert to international format
                int(numbers)
                node[item.attrib['k']] = '+1-' + numbers[0:3] + '-' + numbers[3:6] + '-' + numbers[6:]
            except:     #if not numbers, skip value
                continue
        elif item.attrib['k'] == 'cuisine':     #Lowercase and format cuisine
            node[item.attrib['k']] = item.attrib['v'].lower().replace('_',  ' ').replace(', ', ';').replace(',', '').strip().replace(' ', '_')
        elif item.attrib['k'] == 'brand':       #Capitalize brand names
            node[item.attrib['k']] = item.attrib['v'].title()
        elif item.attrib['k'] == 'natural':     #Skip website URL found in 'natural'
            if item.attrib['v'] == 'http://baywestsupply.com/':
                continue
            else:
                node[item.attrib['k']] = item.attrib['v']
        elif item.attrib['k'] == 'route':   #Skip non access values in 'route'
            if item.attrib['v'] == '101' or item.attrib['v'] == '299':
                continue
            else:
                node[item.attrib['k']] = item.attrib['v']
        else:       #Put in as is if nothing special is specified for that key
            node[item.attrib['k']] = item.attrib['v']

def shape_element(element):
    if element.tag == "node" or element.tag == "way":
        #Get root values
        global node
        node = get_root_values(element)
        #Create dictionaries for storing tag values to be nested
        global nests
        nests = {}
        for tag in nesttags:
            nests[tag] = {}
        #Correct tags and organize tags in dictionaries
        process_tags(element)
        #Nest dictionaries if values found
        for field in nests.keys():
            if len(nests[field]) > 0:
                node[field] = nests[field]
        #Return completed node
        return node
    else:
        return None

#Compile elements into list, write list to JSON file
def process_map(file_in):
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)

        fo.write(json.dumps(data))

process_map(datafile)