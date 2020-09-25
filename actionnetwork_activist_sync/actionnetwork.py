# -*- coding: utf-8 -*-
"""Interacts with ActionNetwork API

https://actionnetwork.org/docs
"""

from pyactionnetwork import ActionNetworkApi

from actionnetwork_activist_sync.osdi import Person

class ActionNetwork(ActionNetworkApi):
    """Helper class to interact with the ActionNetwork API

    Expects env var to be set
    """

    def __init__(self,api_key):
        super().__init__(api_key=api_key)

    def remove_member_by_email(self, email):
        """Update custom field that flags membership (is_member)

        Args:
            email (str): email address to update

        Returns:
            list of Person objects with updated data
        """

        updated_people = []
        people = self.get_people_by_email(email)
        for person in people:
            response = self.update_person(
                person_id=person.get_actionnetwork_id(),
                custom_fields={'is_member': 'False'}
            )
            updated_people.append(Person(**response))
        return updated_people

    def get_people_by_email(self, email):
        """Search for people by email

        Args:
            email (str): email address to update

        Returns:
            list of Person objects with updated data
        """

        response = self.get_person(search_string=email)
        return [Person(**p) for p in response['_embedded']['osdi:people']]
