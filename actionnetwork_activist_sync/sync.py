# -*- coding: utf-8 -*-
"""
'Main' controller that does the sync
"""

from actionnetwork_activist_sync.actionkit_export import ActionKitExport
from actionnetwork_activist_sync.actionnetwork import ActionNetwork
from actionnetwork_activist_sync.debug import PersonCompare
from actionnetwork_activist_sync.field_mapper import FieldMapper
from uszipcode import SearchEngine




def sync(path, previous_date, current_date,branches,dry_run=True):
    """
    The 'main' function that gets invoked by AWS Lambda.

    Performs three main tasks:

    - Deactivate people who were on the old list, but not the new list
    - Update people who are on both lists
    - Create people who were not on the old list, but are on the new list
    """
    # search engine object to translate zipcodes to counties
    search = SearchEngine(simple_zipcode=True)
    # dict to hold each branch's ActionNetwork object
    actionnetwork_dict = {}

    branch_apis = {'DC': 'adc35ecc62127c367a0d4ff6d80d4aaf',
                   'MOCO': '35fafdb312f073b2477d7535fe10e531',
                   'PGC': 'dd0a692686682295025cc9d2f126cbf4',
                   'NOVA': '0054bd054c8338e26d45428a9cdec7f5'
                   }
    for branch in branches:
        if branch in list(branch_apis.keys()):
            actionnetwork_dict[branch] = ActionNetwork(api_key=branch_apis[branch])
        else:
            print(f"Unknown Branch {branch}")

    # TODO: come up with some system for keeping track of this
    actionkit_export = ActionKitExport(zipsearch=search,path=path,previous_date=previous_date,current_date=current_date)
    actionkit_export.load()
    actionkit_export.filter_missing_email()
    actionkit_export.clean()

    for index, row in actionkit_export.missing_email.iterrows():
        print('Missing email: {} {}'.format(row['first_name'], row['last_name']))
        if not dry_run:
            # TODO: figure out named based matching
            pass

    for i in actionnetwork_dict:
        actionnetwork = actionnetwork_dict[i]
        print(f'Running {i} Branch update')

        # People where are no longer in the current spreadsheet, but were
        # in the previous one have had their membership lapse.
        members_left_branch_df = actionkit_export.get_previous_not_in_current()
        members_left_branch_df = members_left_branch_df.loc[actionkit_export.get_previous_not_in_current()['County']==i]
        current_branch_df = actionkit_export.current_df.loc[actionkit_export.current_df['County'] == i]

        for index, row in members_left_branch_df.iterrows():

            field_mapper = FieldMapper(row)

            people = actionnetwork.get_people_by_email(row['Email'])
            for existing_person in people:
                field_mapper.person_id = existing_person.get_actionnetwork_id()
                updated_person = field_mapper.get_actionnetwork_person()

                print('Leaving person: ', field_mapper.exported_person['Email'],field_mapper.person_id)
                comp = PersonCompare(existing_person, updated_person)
                comp.print_diff()
                print()
                if not dry_run:
                    actionnetwork.update_person(**updated_person)

        for index, row in current_branch_df.iterrows():

            field_mapper = FieldMapper(row)

            people = actionnetwork.get_people_by_email(row['Email'])
            if len(people) == 0:
                person = field_mapper.get_actionnetwork_person()
                print('New member: {}'.format(person['email']))
                if not dry_run:
                    actionnetwork.create_person(**person)
            else:
                for existing_person in people:
                    field_mapper.person_id = existing_person.get_actionnetwork_id()
                    updated_person = field_mapper.get_actionnetwork_person()

                    print('Updating person: ', field_mapper.exported_person['Email'],field_mapper.person_id)
                    comp = PersonCompare(existing_person, updated_person)
                    comp.print_diff()
                    print()
                    if not dry_run:
                        actionnetwork.update_person(**updated_person)

    return {
        'statusCode': 200,
        'body': 'Sync Complete'
    }
