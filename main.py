import numpy as np
import matplotlib.pyplot as plt

x_domain, y_domain = np.linspace(-2, 2, 500), np.linspace(-2, 2, 500)
bound = 2
max_iterations = 100
colormap = "nipy_spectral"

func = lambda z, p, c: z**p + c


iteration_array = []
for y in y_domain:
    row = []
    for x in x_domain:
        z = 0
        p = 2
        c = complex(x, y)
        for iteration_number in range(max_iterations):
            if abs(z) >= bound:
                row.append(iteration_number)
                break
            else:
                try:
                    z = func(z, p, c)
                except (ValueError, ZeroDivisionError):
                    z = c
        else:
            row.append(0)

    iteration_array.append(row)

ax = plt.axes()
ax.set_aspect("equal")
graph = ax.pcolormesh(x_domain, y_domain, iteration_array, cmap=colormap)
plt.colorbar(graph)
plt.xlabel("Real-Axis")
plt.ylabel("Imaginary-Axis")
plt.show()