import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

all_dfs = []

def plot(df, name):
    print(df)

    median_values = df.mean()
    df = df[median_values.sort_values().index]

    plt.rcParams.update({'font.size': 24})
    plt.figure(figsize=(32, 12))

    ax = sns.violinplot(df, inner=None, alpha=0.1)
    plt.ylim(0, 2000)
    sns.stripplot(df, jitter=False, size=15, ax=ax, alpha = 0.5)
    plt.ylabel("cycles per interrupt handling", fontsize=30)
    plt.xlabel("system configuration", fontsize=30, labelpad=50)

    # Get the current tick labels and positions
    labels = plt.gca().get_xticklabels()
    positions = range(len(labels))

    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()
    plt.savefig(f"{name}.png", dpi=600)
    plt.close()


def gather_data(test_name):
    all_data = []

    print(f"plotting data from: {test_name}")

    # load data
    for filename in os.listdir(test_name):
        # Join the folder path with the filename to get the full path
        file_path = os.path.join(test_name, filename)
        
        # read all lines
        lines = open(file_path, "r").read().split('\n')
        # remove empty lines
        lines_filtered = list(filter(lambda a: len(a) > 0, lines))
        # extract durations
        data = list(map(lambda a: int(a.split()[-1]), lines_filtered))
        # add to data list
        all_data.append([filename] + data)

    # find max length
    max_length = max(len(inner_list) for inner_list in all_data)
    all_data = list(map(lambda a: a+(max_length-len(a))*[None], all_data))

    # create dataframe
    data_dict = {
        a[0] : a[1::] for a in all_data
    }
    df = pd.DataFrame(data_dict)

    all_dfs.append(df)

    plot(df, test_name.split('/')[1] + "_" + test_name.split('/')[-1])
    

for entry in os.scandir("log"):
    if entry.is_dir():  # Check if the entry is a directory
        print(entry.name)  # Print the name of the directory

        # List to store the directories
        directories = []

        # Walk through the root folder
        for root, dirs, files in os.walk(f"log/{entry.name}"):
            # Check if the current path is exactly two levels deep
            if root.count(os.sep) == 3:
                directories.append(root)

        for f in directories:
            gather_data(f)

        # plot combined statistics
        merged_df = pd.concat(all_dfs, ignore_index=True)
        plot(merged_df, f"{entry.name}_all")