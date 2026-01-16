import pandas as pd

data = {
    "Name1": ["Alice", "Bob", "Charlie", "David", "Eve"],
    "Name2": ["Alice2", "Bob2", "Charlie2", "David2", "Eve2"],
    "Dept":  ["IT", "Sales", "IT", "HR", "Sales"]
}


df = pd.DataFrame(data)






df_t = df.columns.get_loc("Dept")
print(df_t)