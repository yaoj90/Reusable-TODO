"""
Reusable Todo list app
"""
import streamlit as st
from google.oauth2 import service_account
from gsheetsdb import connect
from gspread_pandas import Client
import gspread
from oauth2client.service_account import ServiceAccountCredentials as sac
import pandas as pd

# Connect to google sheet
def gsheet2df(spreadsheet_name):
    # Create a Google Authentication connection object
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = Client(scope=scope, creds=credentials)

    sheet = client.open(spreadsheet_name)
    return sheet

# reset to the default list, which may be done or half done before, all items are now set to be 'TODO'
def reset(worksheet):
    df = pd.DataFrame.from_dict(worksheet.get_all_values())
    for i, todo_text in enumerate(df.values[1:]):
        if todo_text[1] != "TODO":
            worksheet.update(f'A{i + 2}:B{i + 2}', [[todo_text[0], "TODO"]])


# create or select a worksheet named 'todolist'
def createORsearchSheet(todolist):
    try:
        worksheet = sheet.worksheet(todolist)
    except:
        worksheet = sheet.add_worksheet(title=todolist, rows=100, cols=2)
        worksheet.update('A1:B1', [[todolist, "Status"]])  # set the A1 cell to be the todolist
    return worksheet


# find distinct todo lists
def findList(worksheet_list):
    distinct = []
    for worksheet in worksheet_list:
        distinct.append(worksheet.acell('A1').value)
    return distinct


# edit items in a todo list
def edit(worksheet):
    df = pd.DataFrame.from_dict(worksheet.get_all_values())

    if 'todo_items' not in st.session_state.keys():
        todo_items = []
        for i, todo_text in enumerate(df.values[1:]):
            todo_items.append(f'{todo_text[0]}')
        st.session_state['todo_items'] = todo_items
    else:
        todo_items = st.session_state['todo_items']


    with st.form('myform', True):
        todo = st.text_input("Add item", key="form")
        input = [todo, "TODO"]

        col1, col2, col3 = st.columns(3)
        with col1:
            # Add item
            if st.form_submit_button(label="Add"):
                worksheet.update(f'A{len(df.index) + 1}:B{len(df.index) + 1}', [input])
                todo_items.append(todo)
        with col2:
            # set default list
            if st.form_submit_button(label="Default",
                                     help="Set the shown list on the rightside to be the default list"):
                # list all items with "TODO" status
                i = 2
                for todo_text in df.values[1:]:
                    if todo_text[1] == "TODO":
                        worksheet.update(f'A{i}:B{i}', [todo_text.tolist()])
                        i += 1
                # delete items without "TODO" status
                for j in range(i, len(df.index) + 1):
                    worksheet.update(f'A{j}:B{j}', [["", ""]])

        with col3:
            # reset to be the default list
            if st.form_submit_button(label="reset", help="Reset the list to be the default list, status of all items will be set to TODO"):
                reset(worksheet)

    ## Display the contents of todolist
    df = pd.DataFrame.from_dict(worksheet.get_all_values())
    # update the status of checked items to "Done"
    for i in st.session_state.keys():
        if st.session_state[i]:
            for j, todo_text in enumerate(df.values[1:]):
                if i == 'dynamic_checkbox_' + f'{todo_text[0]}':
                    worksheet.update(f'A{j+2}:B{j+2}', [[todo_text[0], "Done"]])

    # display items with status "TODO"
    df = pd.DataFrame.from_dict(worksheet.get_all_values())
    for i, todo_text in enumerate(df.values[1:]):
        if todo_text[1] == "TODO":
            st.checkbox(f'{todo_text[0]}', key='dynamic_checkbox_' + f'{todo_text[0]}')


## Information of this app
st.title("Reusable Todo list app")
st.text("Made by Yao J. Galteland")
st.subheader("This app is suitable for reusing a todo list, such as travel packing checklist and grocery list. Click "
             "\"Default\" to set a displayed check list to be the default list. Click \"Reset\", the list will be set to "
             "the default list, all items will have the status \"TODO\". In other words, each time when you want to "
             "reuse a list, please click \"Reset\".")

## connect the google sheet
sheet = gsheet2df('streamli_demo')
worksheet_list = sheet.worksheets()

## side bar information and options
st.sidebar.text("Edit: edit (including add, delete items) a chosen list")
st.sidebar.text("Create: create a new list")
st.sidebar.text("Delete: delete a chosen list")
menu = ["Edit", "Create", "Delete"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Edit":
    with st.sidebar:
        todolist = st.sidebar.selectbox("Existing Lists", findList(worksheet_list))
        worksheet = createORsearchSheet(todolist)
    edit(worksheet)

elif choice == "Create":
    with st.sidebar:
        todolist = st.text_input("Add task", key="task").upper()
        is_submit = st.button(label="submit")

    if is_submit:
        worksheet = createORsearchSheet(todolist)

elif choice == "Delete":
    with st.sidebar:
        todolist = st.selectbox("Existing Tasks", findList(worksheet_list))
        is_submit = st.button(label="submit")
    if is_submit:
        worksheet = createORsearchSheet(todolist)
        sheet.del_worksheet(worksheet)