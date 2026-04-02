
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("trajectory.csv")

fig = plt.figure()
ax = fig.add_subplot(projection='3d')

for tid in df["id"].unique():
    d = df[df["id"]==tid]
    ax.plot(d["x"], d["y"], d["z"], label=f"ID {tid}")

ax.set_xlabel("X")
ax.set_ylabel("Y")
ax.set_zlabel("Z")
ax.legend()
plt.show()
