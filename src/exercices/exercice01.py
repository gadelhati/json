import numpy as np

# objeto criado pelo NumPy, numpy.ndarray bidimensional com valores de temperatura
temperatura = np.array([
    [24.1, 24.5, 25.0],
    [23.8, 24.2, 24.9],
    [23.5, 24.0, 24.6]
])

print(temperatura)
print(type(temperatura))
# eixos: 3 linhas × 3 colunas
print("shape:", temperatura.shape)
# dimensões: 2
print("dimensões:", temperatura.ndim)
# como os valores são armazenados
print("tipo:", temperatura.dtype)

# axis