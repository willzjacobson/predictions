import pandas as pd


def cleaner(xlsx_location, building_num):
    clean = pd.read_excel(xlsx_location)
    clean = clean[clean.Building == building_num]
    clean['Recommendation_DateTime'] = pd.to_datetime(
            clean["Recommendation_DateTime"])

    clean['Actual_DateTime'] = pd.to_datetime(
            clean["Actual_DateTime"])

    clean = clean.drop(axis=1,
                       labels=['Comfort_Zone_Percentage', 'ID', 'Building'])

    clean = clean.dropna(axis=0, subset=['Agreed', 'Recommendation_DateTime',
                                         'Actual_DateTime'])

    clean = clean[pd.notnull(clean['Recommendation_DateTime']) &
                  pd.notnull(clean['Actual_DateTime'])]

    return clean


df1 = cleaner(None, 345)
df2 = cleaner(None, 345)
new = df1.append(df2)
new = new.drop_duplicates(subset=['Actual_DateTime'])
new = new.sort_values(by=['Actual_DateTime'])
