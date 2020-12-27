import pandas as pd
import numpy as np
import requests
import datetime
from actionnetwork_activist_sync.actionnetwork import ActionNetwork

def get_all_people(api=None, people=None, url="https://actionnetwork.org/api/v2/people",i=0):
    if not people:
        people = []
    data = requests.get(url=url, headers=api.headers)
    people += [d for d in data.json()['_embedded']['osdi:people']]

    if data.json().get('_links', {}).get('next', None):
        next_url = data.json().get('_links').get('next').get('href')
        i += 1
        return get_all_people(api=api, people=people, url=next_url,i=i)
    return people
def full_member_pull():
    branch_apis = {'DC': 'adc35ecc62127c367a0d4ff6d80d4aaf',
                   'MOCO': '35fafdb312f073b2477d7535fe10e531',
                   'PGC': 'dd0a692686682295025cc9d2f126cbf4',
                   'NOVA': '0054bd054c8338e26d45428a9cdec7f5'
                   }
    actionnetwork_dict = {}
    for branch in list(branch_apis.keys()):
        if branch in list(branch_apis.keys()):
            actionnetwork_dict[branch] = ActionNetwork(api_key=branch_apis[branch])
        else:
            print(f"Unknown Branch {branch}")

    email_dfs = []
    for api in actionnetwork_dict.values():
        all_people = get_all_people(api=api)
        email = []
        phone = []
        ad = []
        for person in all_people:
            for address in person['email_addresses']:
                email.append(address['address'])
            for number in person['phone_numbers']:
                if number['primary'] == True:
                    try:
                        phone.append(number['number'])
                    except:
                        phone.append(np.nan)
            for address in person['postal_addresses']:
                if address['primary'] == True:
                    try:
                        ad.append(address['address_lines'][0])
                    except:
                        ad.append(np.nan)
        df = pd.json_normalize(all_people)
        df['email_address'] = email
        df['phone_number'] = phone
        df['address'] = ad
        drop_cols = ['email_addresses','phone_numbers','postal_addresses','identifiers','created_date','modified_date',
                     'languages_spoken', '_links.self.href','_links.osdi:signatures.href',
                     '_links.osdi:submissions.href','_links.osdi:donations.href', '_links.osdi:taggings.href',
                     '_links.osdi:outreaches.href','_links.osdi:attendances.href']
        df.drop(drop_cols,axis=1,inplace=True)
        df.to_csv(f'ActionNetwork_full_member_export_{datetime.datetime.now().date()}.csv',index=False)
        email_dfs.append(df['email_address'])
    totdf = pd.concat(email_dfs)
    totdf.drop_duplicates().to_csv(f'ActionNetwork_full_member_email_export_{datetime.datetime.now().date()}.csv',
                                   index=False,header=False)

if __name__ == "__main__":
    full_member_pull()
