###############################################################################
# Program to calculate required parts to be ordered to build 'n' number of
# desired products.  It requires selecting a CSV file exported from Parts and
# Vendors with accurate quantities.  It is assumed the desired product to build
# is the top level item. 
#
# By: Nathan Miller
# Date: June 7th, 2022
# Version: 1.0
###############################################################################

import tkinter as tk
import tkinter.filedialog as fd
import tkinter.scrolledtext as tkscrolled
import os
import pandas as pd
from anytree import Node, PreOrderIter

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

# Window Size Constants
START_HEIGHT = 1280 
START_WIDTH =  720
MIN_HEIGHT = int(START_HEIGHT / 4)
MIN_WIDTH =  int(START_WIDTH / 4)
xSpacing = 10
ySpacing = 10

# Create home screen
Gui_Home_Screen = tk.Tk(className=' Purchase Assembly Needs Calculator')
Gui_Home_Screen.minsize(height=MIN_HEIGHT, width=MIN_WIDTH)
Gui_Home_Screen.geometry(str(START_HEIGHT) + 'x' + str(START_WIDTH))
Gui_Home_Screen.state('zoomed') #Maximize the window

# Configure rows
tk.Grid.rowconfigure(Gui_Home_Screen, index=0, weight=1)
tk.Grid.rowconfigure(Gui_Home_Screen, index=1, weight=1)
tk.Grid.rowconfigure(Gui_Home_Screen, index=2, weight=1)
tk.Grid.rowconfigure(Gui_Home_Screen, index=3, weight=10)

# Configure columns
tk.Grid.columnconfigure(Gui_Home_Screen, index=0, weight=1)
tk.Grid.columnconfigure(Gui_Home_Screen, index=1, weight=1)
tk.Grid.columnconfigure(Gui_Home_Screen, index=2, weight=1)
tk.Grid.columnconfigure(Gui_Home_Screen, index=3, weight=1)
tk.Grid.columnconfigure(Gui_Home_Screen, index=4, weight=30)

# Units labels
tk.Label(Gui_Home_Screen, text="# Units1:").grid(row=0, 
                                                 column=0, 
                                                 padx=xSpacing, 
                                                 pady=ySpacing)

# File path labels
path_label0 = tk.Label(Gui_Home_Screen, text="No file selected.")
path_label0.grid(row=0, column=3, padx=xSpacing, pady=ySpacing)

# Units entry box
eb_units0 = tk.Entry(Gui_Home_Screen, width=20)
eb_units0.grid(row=0, column=1, padx=xSpacing, pady=ySpacing)

# Add file buttons
parts_button0 = tk.Button(Gui_Home_Screen,
                         text='Choose Parts and Vendors CSV File', 
                         command=lambda: selectFileClick(path_label0)).grid(row=0,
                                                                            column=2,
                                                                            sticky=tk.W,
                                                                            padx=xSpacing,
                                                                            pady=ySpacing)

# Text box for displaying results
tb_result = tkscrolled.ScrolledText(Gui_Home_Screen, width=150, height=40, wrap='none')
tb_result.grid(row=3, column=0, columnspan=6, padx=xSpacing, pady=ySpacing)
                                                                            
                                                                            
def selectFileClick(path_label):
    file_path = fd.askopenfilename(initialdir=os.getcwd(),
                                   title="Select the CSV file",
                                   filetypes=(("csv files","*.csv"),))
    
    # If the user selected a file
    if file_path:
        # If the user didn't pick a CSV file
        if '.csv' not in file_path:
            path_label['text'] = 'You must select a csv file.'
        else:
            path_label['text'] = file_path
    
    # Else the user did not select a file
    else:
        path_label['text'] ='No file selected.'


def load_data():
    # Delete any old text from the result text box
    tb_result.delete("1.0", tk.END)
    
    # If no file selected
    if '.csv' not in path_label0['text']:
        tb_result.insert(tk.END, 'No file selected.')
        
    # Else file selected
    else:
        load_data_file()    
    
    
def load_data_file():
    # Read in the parts data
    inventory = pd.read_csv(path_label0['text'], encoding='latin_1')

    # Fill in blanks in the Detail, 'Qty', and 'U/M' columns so we don't lose the data later
    inventory.fillna({'Detail':'Keep', 'Qty':1, 'U/M':'each'}, inplace=True)

    # Drop rows that are 'Supplied by Vendor' or 'Datasheet' in the 'Detail' column
    inventory = inventory[inventory['Detail'].str.contains('Supplied by Vendor')==False]
    inventory = inventory[inventory['Detail'].str.contains('Datasheet')==False]

    # Drop rows without numeric data in the 'Qty' column
    inventory['temp'] = inventory['Qty'].apply(pd.to_numeric, errors='coerce')
    inventory = inventory[inventory['temp'].notna()]

    # Drop 'Detail' and 'Temp' columns
    inventory.drop(columns=['Detail'], inplace=True)
    inventory.drop(columns=['temp'], inplace=True)
    
    # Reset the index
    inventory = inventory.reset_index(drop=True)
    
    # Duplicate the stock column
    inventory['current_stock'] = inventory['Stock']
    
    # Call function to build the tree
    build_tree(inventory=inventory, units_to_build=int(eb_units0.get()))


def build_tree(inventory, units_to_build):

    # Add the root node
    root = Node(inventory['P/N'][0], 
                part_number=inventory['P/N'][0],
                title=inventory['Title'][0], 
                Type=inventory['Type'][0],
                current_stock=inventory['current_stock'][0],
                num_needed=units_to_build,
                um=inventory['U/M'][0],
                lead_time=inventory['Leadtime'][0],
                indent_level=inventory['Indent Level'][0])
    
    # Current node pointer
    current = root
    
    # Add each row of inventory dataframe to tree
    for i in range(1, inventory.shape[0]):  
        new_node = Node(inventory['P/N'][i],
                        part_number=inventory['P/N'][i],
                        parent=current,
                        title=inventory['Title'][i], 
                        Type=inventory['Type'][i],
                        um=inventory['U/M'][i],
                        lead_time=inventory['Leadtime'][i],
                        current_stock=inventory['current_stock'][i],
                        indent_level=inventory['Indent Level'][i])
        
        # Get the number needed and update the current stock in inventory (if we take from it)
        number_needed = float(inventory['Qty'][i]) * current.num_needed
        number_in_stock = float(inventory['Stock'][i])
        
        if number_in_stock >= number_needed:
            new_node.num_needed = 0
            inventory['Stock'][i] = number_in_stock - number_needed
        else:
            new_node.num_needed = number_needed - number_in_stock
            inventory['Stock'][i] = 0
        
        # Move the node pointer to the forward or backward depending on the next indent level
        if i < inventory.shape[0] - 1:
            # If the next node will be a child of new_node, set new_node to be current 
            if new_node.indent_level < inventory['Indent Level'][i + 1]:
                current = new_node
            elif new_node.indent_level != inventory['Indent Level'][i + 1]:        
                while (current.indent_level != 0) and (current.indent_level >= inventory['Indent Level'][i + 1]):
                    current = current.parent  

    # Use temporary list in order to put the tree back into a dataframe
    rows = []
    for node in PreOrderIter(root):
        rows.append((node.Type, node.part_number, node.title, node.current_stock, node.num_needed, node.um, node.lead_time))
    
    # Create dataframe     
    df = pd.DataFrame(rows, columns=('type', 
                                     'part_number', 
                                     'title', 
                                     'current_stock', 
                                     'num_needed', 
                                     'um', 
                                     'lead_time'))
    
    # Aggregate by part_number
    df.groupby(['type', 
                'part_number', 
                'title', 
                'current_stock', 
                'um', 
                'lead_time'], as_index=False)['num_needed'].sum()
    
    # Sort the dataframe 
    df.sort_values(['type', 'part_number'], ascending=[True, True], inplace=True)
    
    # Drop rows with 0 needed parts
    df = df[df.num_needed != 0]
    
    # Reset the index
    df = df.reset_index(drop=True)
    
    # Save results to csv
    df.to_csv(r'results.csv', index=False)
    
    # Display the results on the screen
    tb_result.insert(tk.END, df.to_string(index=False))

# Start button
start_button = tk.Button(Gui_Home_Screen,
                         text='Click to Run', 
                         command=load_data).grid(row=0,
                                                 column=4,
                                                 sticky=tk.W,
                                                 padx=xSpacing,
                                                 pady=ySpacing)                                                                            

      
if __name__ == "__main__":
    #start main loop and show form
    Gui_Home_Screen.mainloop()                                            
                                                 