
class UndoRedoAction:
    def __init__(self, function, *args):
        self.function = function
        self.args = args
    def execute(self):
        self.function(*self.args)

class UndoRedoManager:
    def __init__(self):
        self.undo_stack = []
        self.redo_stack = []
        self.state = 'D'

    def pushAction(self, action):
        print(f'Adding action during {self.state}')
        if self.state == 'U':
            self.redo_stack.append(action)
        elif self.state == 'D':
            self.redo_stack = []
            self.undo_stack.append(action)
        else: # self.state == 'R'
            self.undo_stack.append(action)

    def undo(self):
        print(f'Undo during {self.state}')
        if self.undo_stack != []:
            self.state = 'U'
            action = self.undo_stack.pop()
            action.execute()
            self.state = 'D'
        else:
            print("Nothing to Undo!")

    def redo(self):
        print(f'Redo during {self.state}')
        if self.redo_stack != []:
            self.state = 'R'
            action = self.redo_stack.pop()
            action.execute()
            self.state = 'D'
        else:
            print("Nothing to Redo!")

