import re, sys, json

diameter_apps = {
    'CIP_IP': {'Vendor_ID': '193', 'AppID_Type': 'Authentication', 'AppID_Value': '16777232', 'Service_Context_ID': '*', 'Req_Res': 'CIP_IP'},\
    'Gx': {'Vendor_ID': '10415', 'AppID_Type': 'Authentication', 'AppID_Value': '16777238', 'Service_Context_ID': '*', 'Req_Res': 'Gx'},\
    'ESy':{'Vendor_ID': '193', 'AppID_Type': 'Authentication', 'AppID_Value': '16777304', 'Service_Context_ID': '*', 'Req_Res': 'ESy'}\
    }

OCC_configurations = {
    'FE': {'apps': ['Gx', 'ESy']},\
    'BE': {'apps': ['CIP_IP', 'Gx', 'ESy']},\
    'AF': {}
    }

templates = {'FE_app_template': 'Diameter Front-End.Definition of Peers.Applications=matrix:{{IN# {}# {}# {}# {}# {}# {}}}',\
    'BE_app_template': 'SDP Diameter Back-End.Definition of Peers.Applications=matrix:{{OUT# {}# {}# {}# {}# {}# {}}}',\
    'BE_peers_template': 'SDP Diameter Back-End.Definition of Peers.Peers=matrix:{{{},{},{}# {}# {}# true# # Static# Disconnected# true}}',\
    'BE_roundrobin_app_template': 'SDP Diameter Back-End.Definition of Peers.Outgoing Request Routing=matrix:{{200# ROUNDROBIN# {}# {}, {}#  }}',\
    'BE_roundrobin_peer_template': 'SDP Diameter Back-End.Definition of Peers.Outgoing Request Routing=matrix:{{200# ROUNDROBIN# {}# {}:{}#  }}',\
    'AF_template': 'Parameter Directory.Parameters=matrix:{{AF-Response-SDP{}.cs.# {}# String}}'\
    }

SDP_members = ['A', 'B']
line_entries = {"1_19089-CXC_1730371": [], "4_19089-CXC_1730371": [], "7_19089-CXC_1730371": []}
SDPs = []

def fill_template(template, *argv):
    return template.format(*argv)

def add_SDP_entry():
    SDPs.append({'SDP_realm': ''})
    for member in SDP_members:
        SDPs[-1][member] = {'hostname': '', 'Blue': '', 'Red': '', 'Port': '3868', 'Transport': 'SCTP'}

def read_SDP_realm():
    SDPs[-1]['SDP_realm'] = input('\n\nEnter SDP realm\n')

def read_SDP_member_hostname(member):
    SDPs[-1][member]['hostname'] = input('\n\nEnter SDP Member {} hostname\n'.format(member))

def read_SDP_member_IPs(member):
    IPs = ['Red', 'Blue']
    for i in IPs:
        SDPs[-1][member][i] = input('\n\nEnter SDP Member {} {} IP\n'.format(member, i))

def conf_app(conf):
    choice = input('\n\nEnter "1" to configure all apps {}\nor Enter apps list comma separated\n'.format(OCC_configurations[conf]['apps']))
    apps = OCC_configurations[conf]['apps'] if choice == '1' else [x.strip() for x in choice.split(',')]
    apps_list = [fill_template(templates[conf+'_app_template'], SDPs[-1]['SDP_realm'], *diameter_apps[app].values()) for app in apps]

    return apps_list, apps

def conf_roundrobin(app):
    group = []
    group.append(fill_template(templates['BE_roundrobin_app_template'], 'app',\
        SDPs[-1]['SDP_realm'], diameter_apps[app]['AppID_Value']))
    for member in SDP_members:
        group.append(fill_template(templates['BE_roundrobin_peer_template'], 'peer',\
        SDPs[-1][member]['hostname'], SDPs[-1][member]['Port']))

    return group

def FE_line_enteries():
    line_entries['1_19089-CXC_1730371'].append(conf_app('FE')[0])
    
def BE_line_enteries():
    # Apps definition
    SDP_BE_dict = {'application': [], 'peers': [], 'roundrobin': []}
    conf_app_list = conf_app('BE')
    SDP_BE_dict['application'] = conf_app_list[0]
    # Peers definition
    for member in SDP_members:
        read_SDP_member_hostname(member)
        read_SDP_member_IPs(member)
    for member in SDP_members:
        SDP_BE_dict['peers'].append(fill_template(templates['BE_peers_template'], *SDPs[-1][member].values())) 
    # Roundrobin definition
    SDP_BE_dict['roundrobin'] = [conf_roundrobin(app) for app in conf_app_list[1]]  
    line_entries["4_19089-CXC_1730371"].append(SDP_BE_dict)

def AF_line_enteries():
    line_entries['7_19089-CXC_1730371'].append(fill_template(templates['AF_template'],\
        re.search('SDP(.*)V\.Vodafone\.com', SDPs[-1]['SDP_realm']).group(1), SDPs[-1]['SDP_realm']))

option = 'c'
if len(sys.argv) == 1:
    while option != 'e':
        option = input('Enter "1" to define an SDP\nor to terminate enter "e"\n')
        if option == '1':
            add_SDP_entry()
            choice = input('\n\nEnter "1" to configure {}\nor Enter configurations list comma separated\n'.format(list(OCC_configurations.keys())))
            confs = OCC_configurations.keys() if choice == '1' else [x.strip() for x in choice.split(',')]
            read_SDP_realm()
            for conf in confs:
                locals()[conf+'_line_enteries']()
        elif option == 'e':
            break

    with open('line_entries.yml', 'w') as output_file:
        json.dump({'line_entries': line_entries}, output_file, indent=4)
