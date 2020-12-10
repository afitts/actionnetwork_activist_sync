# -*- coding: utf-8 -*-
"""Converts ActionKit Excel exports to Agate tables"""

import pandas as pd

class ActionKitExport:
    """ActionKitExport converts two ActionKit Excel spreadsheets.

    The reason there are two is so we can calculate who is missing in
    the new sheet and who are new members.

    Args:

    Attributes:
        previous_df (pandas.DataFrame): The previous CSV after conversion
        current_df (pandas.DataFrame): The newest CSV after conversion
        missing_email (pandas.DataFrame): Rows that were missing an email
    """

    def __init__(self,zipsearch,path,previous_date,current_date):
        self.previous_df = None
        self.current_df = None
        self.missing_email = None
        self.zipsearch = zipsearch
        self.path = path
        self.previous_date = pd.to_datetime(previous_date).strftime('%m/%d/%y')
        self.current_date = pd.to_datetime(current_date).strftime('%m/%d/%y')

    def load(self) -> None:
        """Converts the CSVs to pandas tables"""
        pdate = self.previous_date.replace('/','.')
        cdate = self.current_date.replace('/','.')
        previous_file = f'{self.path}metro_dc_membership_list-{pdate}.csv'
        current_file = f'{self.path}metro_dc_membership_list-{cdate}.csv'
        self.previous_df = pd.read_csv(previous_file,header=0)
        self.current_df = pd.read_csv(current_file,header=0)

    def filter_missing_email(self) -> None:
        """Strips out and saves rows that are missing emails"""
        self.missing_email = self.current_df[self.current_df['Email'].isna()]
        self.previous_df = self.previous_df[self.previous_df['Email'].notna()]
        self.current_df = self.current_df[self.current_df['Email'].notna()]

    def get_previous_not_in_current(self) -> pd.DataFrame:
        """Finds rows that were missing in the current CSV"""
        # Outer join of previous CSV and current CSV
        jf = self.current_df.merge(self.previous_df,on='Email',how='outer')

        # Grab rows in self.previous_df that aren't in self.current_df. Drop duplicate rows that end in _x.
        no_longer_current_member_df = jf.loc[jf['AK_ID_x'].isna()]\
            .drop([c for c in jf.columns if c.endswith("_x")],axis = 1)

        # Cut off '_y' in column names from join
        for i in [c for c in jf.columns if c.endswith("_y")]:
            no_longer_current_member_df[i[:-2]] = no_longer_current_member_df[i]
            no_longer_current_member_df.drop(i,axis=1,inplace=True)

        # Changes applied to people who have left the chapter
        no_longer_current_member_df['membership_status'] = ''
        no_longer_current_member_df['Xdate'] = ''
        no_longer_current_member_df['Left Chapter Date'] = pd.to_datetime(self.current_date).strftime('%Y/%m/%d')

        # Random tweak as this member routinely disappears from our roster
        no_longer_current_member_df.drop(no_longer_current_member_df.loc[
                                             (no_longer_current_member_df['last_name'] == 'Bhandarkar')
                                             & (no_longer_current_member_df['first_name'] == 'Pranav')].index,
                                         inplace=True)

        return no_longer_current_member_df

    def clean(self):

        for df,date in [[self.previous_df,self.previous_date],[self.current_df,self.current_date]]: # Maybe just for current_df
            # Drop duplicates. Only focus on Email duplicates as some members are updated within the csv with new field
            # values (see 6/12/20 member csv for an example of this)
            df.drop_duplicates(subset=['Email'],inplace=True)

            # From 12/04/2020 onward, national started providing both billing and mailing addresses
            if pd.to_datetime(date) >= pd.to_datetime('12/04/2020'):
                df['Address_Line_1'] = df['Mailing_Address1']
                df['Address_Line_2'] = df['Mailing_Address2']
                df['City'] = df['Mailing_City']
                df['State'] = df['Mailing_State']
                df['Zip'] = df['Mailing_Zip']
                # Not all Mailing addresses are filled out? So use Billing if blank
                df.loc[df['Address_Line_1'].isna(), 'Address_Line_2'] = df['Billing_Address_Line_2']
                df.loc[df['Address_Line_1'].isna(), 'City'] = df['Billing_City']
                df.loc[df['Address_Line_1'].isna(), 'State'] = df['Billing_State']
                df.loc[df['Address_Line_1'].isna(), 'Zip'] = df['Billing_Zip']
                df.loc[df['Address_Line_1'].isna(), 'Address_Line_1'] = df['Billing_Address_Line_1']

                df['Country'] = 'United States'

            # Change NaNs to blank
            df.fillna('',inplace=True)

            # Standardize Phone records
            df[['Mobile_Phone','Home_Phone','Work_Phone']] = df[['Mobile_Phone','Home_Phone','Work_Phone']]\
                .replace(r'\-|\(|\)| ','',regex=True)

            # Some Phone records have 2+ numbers in a single field. We'll select the first one.
            df.loc[df['Mobile_Phone'].str.contains(","), 'Mobile_Phone'] = df.loc[df['Mobile_Phone'].str.contains(","),
                                                                                  'Mobile_Phone'].str.split(',').str[0]
            df.loc[df['Home_Phone'].str.contains(","), 'Home_Phone'] = df.loc[df['Home_Phone'].str.contains(","),
                                                                              'Home_Phone'].str.split(',').str[0]

            # Keep one phone record per person, preferentially selecting first available from Mobile, Home, then Work.
            df['Phone'] = df['Mobile_Phone']
            df.loc[df['Phone'] == '', 'Phone'] = df.loc[df['Phone'] == '', 'Home_Phone']
            df.loc[df['Phone'] == '', 'Phone'] = df.loc[df['Phone'] == '', 'Work_Phone']
            df.drop(['Mobile_Phone','Home_Phone','Work_Phone'], axis=1, inplace=True)

            # Grab county using zip code
            df['County'] = [self.zipsearch.by_zipcode(x).to_dict()['county'] for x in df['Zip'].str[0:5].values]
            df.loc[(df['County'] == 'District of Columbia'), 'County'] = 'DC'
            df.loc[(df['County'] == 'Prince George\'s County'), 'County'] = 'PGC'
            df.loc[(df['County'] == 'Montgomery County') | (df['County'] == 'Frederick County'), 'County'] = 'MOCO'
            df.loc[~((df['County'] == 'DC') | (df['County'] == 'PGC') | (df['County'] == 'MOCO')), 'County'] = 'NOVA'

            # Action Network API expects [Address_Line_1,Address_Line_2]
            df['Address'] = df[['Address_Line_1','Address_Line_2']].fillna('').values.tolist()

            # On import, pandas makes the AK_ID column an int64. Must be type str to be submitted to the API
            df['AK_ID'] = df['AK_ID'].astype(str)

            # Convert dates YYYY/MM/DD format (necessary for AN to interpret it as a date)
            df['Xdate'] = pd.to_datetime(df['Xdate']).dt.strftime('%Y/%m/%d')
            df['Join_Date'] = pd.to_datetime(df['Join_Date']).dt.strftime('%Y/%m/%d')

            # National reports that a member is expired if their dues expired more than a year ago. But we count them
            # only as expired if their dues expired more than two years ago. They are marked a Member if their dues
            # expired between 1 and 2 years ago and a Member in Good Standing otherwise.
            df['Xdate'] = pd.to_datetime(df['Xdate'])
            #df.loc[df['Xdate'] < pd.to_datetime(date)-pd.to_timedelta(2*365, unit='d'), 'membership_status'] = "Expired"
            #df.loc[(df['Xdate'] > pd.to_datetime(date)-pd.to_timedelta(2*365, unit='d')) &
            #                            (df['Xdate'] <= pd.to_datetime(date)), 'membership_status'] = "Member"
            #df.loc[df['Xdate'] > pd.to_datetime(date), 'membership_status'] = "Member in Good Standing"
            df['Xdate'] = df['Xdate'].dt.strftime('%Y/%m/%d')

            # Individual updates (as members convey updates without actually updating their national profile)
            df.loc[df['Email'] == 'aaron.samsel@nlrb.gov', 'Email'] = 'aaron.samsel@gmail.com'
            df.loc[df['Email'] == 'salimadofo@salim4dc.com', 'Email'] = 'info@salimadofo.com'
            df.loc[df['Email'] == 'nima@kandoo.tech', 'Email'] = 'nima.fatemi@gmail.com'
        # Find which members have an Xdate that has changed (don't include new members)
        jf = self.current_df.merge(self.previous_df, on=['Email','Xdate'],how='left')
        new_xdate_df = jf.loc[jf['AK_ID_y'].isna()]
        self.current_df['Membership Renewed Date'] = ''
        self.current_df['Membership Renewed Date'].iloc[new_xdate_df.index] = pd.to_datetime(self.current_date).strftime('%Y/%m/%d')
        #pd.to_datetime(self.current_df['Xdate'].iloc[new_xdate_df.index])-pd.to_timedelta(365, unit='d')