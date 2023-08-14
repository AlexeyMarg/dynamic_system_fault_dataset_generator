import pandas as pd
import matplotlib.pyplot as plt

path = 'experiment1.csv'

df = pd.read_csv(path, header=0, index_col=0)

print(df.head())

print(df.columns[2])

n_rows = df.shape[1]
fig, axs = plt.subplots(n_rows,1,figsize=(16,9))
fig.tight_layout()
for i in range(n_rows):
    axs[i].plot(df.index.tolist(), list(df.iloc[:, i]))
    axs[i].legend([df.columns[i]], loc=2)
plt.show()
    

