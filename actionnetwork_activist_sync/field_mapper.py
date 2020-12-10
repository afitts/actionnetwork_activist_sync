# -*- coding: utf-8 -*-
"""Logic to convert people data from ActionKit to ActionNetwork"""

class FieldMapper:
    """Map fields from ActionKit to ActionNetwork

    Args:
        exported_person (pandas.Series): Single person record from ActionKit

    Attributes:
        exported_person (pandas.Series): Single person record from ActionKit
        overrides (dict): fields to override
        is_member (str): "True", "False" (API uses strings)
    """

    def __init__(self, exported_person):

        self.exported_person = exported_person.fillna('')
        self.overrides = {}
        self.person_id = None
        self.is_member = 'True'

    def get_actionnetwork_person(self):
        """Main conversion method"""

        person = {
            'email': self.exported_person['Email'],
            'given_name': self.exported_person['first_name'],
            'family_name': self.exported_person['last_name'],
            'address': self.exported_person['Address'],
            'city': self.exported_person['City'],
            'state': self.exported_person['State'],
            'country': self.exported_person['Country'],
            'postal_code': self.exported_person['Zip'],
            'custom_fields': self.get_custom_fields()
        }
        if self.person_id:
            person['person_id'] = self.person_id

        for field, value in self.overrides.items():
            if field in person:
                person[field] = value

            if field in person['custom_fields']:
                person['custom_fields'][field] = value

        return person

    def get_custom_fields(self):
        """Formats custom fields"""
        # 12/04/2020 UPDATE: 'Organization' and 'monthly status'
        custom_fields = {
            'DSAn ID': self.exported_person['AK_ID'],
            'Dues Expiration Date': self.exported_person['Xdate'],
            'Join Date': self.exported_person['Join_Date'],
            'Middle Name': self.exported_person['middle_name'],
            'suffix': self.exported_person['suffix'],
            #'Organization': self.exported_person['Organization'],
            'Phone': self.exported_person['Phone'],
            'union_member': self.exported_person['union_member'],
            'union_name': self.exported_person['union_name'],
            'union_local': self.exported_person['union_local'],
            'membership_type': self.exported_person['membership_type'],
            #'monthly_status': self.exported_person['monthly_status'],
            'membership_status': self.exported_person['membership_status'],
            'student_yes_no': self.exported_person['student_yes_no'],
            'student_school_name': self.exported_person['student_school_name'],
            'YDSA Chapter': self.exported_person['YDSA Chapter']
        }

        if 'Left Chapter Date' in self.exported_person.index:
            custom_fields['Left Chapter Date'] = self.exported_person['Left Chapter Date']

        if self.exported_person['Membership Renewed Date'] != '':
            custom_fields['Membership Renewed Date'] = self.exported_person['Membership Renewed Date']

        return custom_fields
