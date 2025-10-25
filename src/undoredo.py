
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
        # state has three possible values
        # it is used during pushAction() to determine where it's being called.
        # This may need to be updated if actions are handled recursively in the future
        self.state = 'D'

    def pushAction(self, action):
        # 'D' - pushAction() is executing outside of undo() or redo()
        # 'U' - pushAction() is executing during undo()
        # 'R' - pushAction() is executing during redo()
        if self.state == 'U':
            self.redo_stack.append(action)
        elif self.state == 'D':
            self.redo_stack = []
            self.undo_stack.append(action)
        else: # self.state == 'R'
            self.undo_stack.append(action)

    def undo(self):
        self.state = 'U'
        if self.undo_stack != []:
            action = self.undo_stack.pop()
            action.execute()
        else:
            print("Nothing to Undo!")
        self.state = 'D'

    def redo(self):
        self.state = 'R'
        if self.redo_stack != []:
            action = self.redo_stack.pop()
            action.execute()
        else:
            print("Nothing to Redo!")
        self.state = 'D'

