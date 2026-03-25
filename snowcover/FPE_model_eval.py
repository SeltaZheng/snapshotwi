"""
evaluate the model performance from FPE platform
"""
import glob, os

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

dir_in = r'D:\GoogleDrive\Projects_ongoing\snapshotWI\snowcover\FPE_model'
dir_plt = r'D:\GoogleDrive\Projects_ongoing\snapshotWI\snowcover\plt'
dir_p = r'Z:\projects\SnapshotWI\photos\photos_clean'
df = pd.read_csv(f'{dir_in}/PROVISIONAL_FPE_model_results_user_output_2026-03-16_Snowsites.csv')



#%%--------------------------- multi-sites model evaluation -------------------------------------------
set_name = 'multiple_sites'

# step 1: time series plot for each site inside the multi_site set:
df1 = df[df['station_name'] == set_name]
# add separate site ID as a new column
site = df1['filename'].str.split('/').str.get(0)
df1['site'] = site
# deal with photos without site tag:
df_p = pd.read_excel(f'{dir_p}/starting_photo.xlsx')
# for all site with 'yes' in 'upload' column:
folders = df_p.loc[df_p['uploaded'] == 'yes', 'folder']
# get the photo names for files in each folder and assign
for folder in folders:
    files = glob.glob(f'{dir_p}/timelapse/{folder}/*.jpg')
    files = [os.path.basename(x) for x in files]
    # assign proper site name to rows containing same files:
    df1.loc[df1['site'].isin(files), 'site'] = folder

# convert timestamp to proper pd datetime
df1['timestamp'] = pd.to_datetime(df1['timestamp'])
df1['date'] = df1['timestamp'].dt.strftime('%Y-%m-%d')
df1.to_csv(f'{dir_in}/FPE_model_multisites_wt_sitenames.csv', index=False)

# # if plot all sites into one plot
# g = sns.catplot(
#     data=df1, x="date", y="score",
#     col="site", col_wrap=4,
#     kind="point", # Specifies the use of pointplot
#     height=4, aspect=.7
# )
#
# # Add titles to the facets and adjust layout
# g.fig.suptitle('snow cover score', fontsize=14)
# plt.subplots_adjust(top=0.9) # Adjust the figure's top margin for the main title
# plt.show()

# plot one site by another
for site in df1['site'].unique():
    temp = df1[df1['site'] == site]
    temp['date'] = pd.to_datetime(temp['date'])
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(temp['date'], temp['score'], marker='o')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    plt.xticks(rotation=45)
    plt.tight_layout()
    # plt.show()
    plt.savefig(f'{dir_plt}/{site}.png')
    plt.close()

#%%--------------------------- compare the performance for ADAM016-------------------------------------
sites = ['ADAM016', 'timelapse_ADAM016']
df1 = df[df['station_name'].isin(sites)]

photos1 = df1.loc[df1['station_name'] == 'timelapse_ADAM016', 'filename']
photos2 = df1.loc[df1['station_name'] == 'ADAM016', 'filename']

# get the shared files between two sets:
common = set(photos2).intersection(set(photos1))

# further subset:
df_all = df1[(df1['station_name'] == 'ADAM016') & (df1['filename'].isin(common))].reset_index(drop=True)
df_daily = df1[(df1['station_name'] == 'timelapse_ADAM016') & (df1['filename'].isin(common))].reset_index(drop=True)
df_join = pd.merge(df_all, df_daily, on='filename', how='inner')

# scatter plot comparing all vs. daily only photo:
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter(df_join['score_x'], df_join['score_y'])
ax.set_xlabel('All photo model')
ax.set_ylabel('Daily timelapse model')
ax.set_title('ADAM016 model comparison')
plt.tight_layout()
# plt.show()
plt.savefig(f'{dir_plt}/ADAM016_model_comp.png')
plt.close()

