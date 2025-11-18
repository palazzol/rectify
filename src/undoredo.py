
#
#  Action-based Undo/Redo
#
# If you want to create an undoable operation, simply write your code.
# For any undoable operation, create a undoContext() and use pushAction() as many times as needed,
# supplying it with with any function and args needed to undo the each action
# like this:
#
#   with undoContext("Description of Action Group") as uctx:
#       uctx.recordAction(someFunction, arg1, arg2, kwarg1=value1)
#       uctx.recordAction(anotherFunction, argA, argB)
#
# A call to undo() or redo() will trigger the proper stored functions
# to undo or redo the action group as a unit.
#

from enum import Enum
from typing import Callable, Any

from contextlib import AbstractContextManager

# Public API

# Undo an action group, returning its description or empty string if nothing to undo
def undo() -> str:
    return _urm.undoOrRedo('Undo', _UndoRedoManager.Mode.UNDOING, _urm.undo_stack)

# Redo an action group, returning its description or empty string if nothing to redo
def redo() -> str:
    return _urm.undoOrRedo('Redo', _UndoRedoManager.Mode.REDOING, _urm.redo_stack)

# Insures that actions done within the context are recorded together as a unit
def undoContext(desc: str) -> UndoContext:
    return UndoContext(desc)

# This context manager is standard, but with added recordAction() method
# so that actions can be recorded within the context
class UndoContext(AbstractContextManager):
    def __init__(self, desc: str) -> None:
        self.desc = desc

    def __enter__(self) -> UndoContext:
        if _urm.insideContext:
            raise RuntimeError("Nested UndoContext is not supported")
        _urm.insideContext = True
        return self
    
    def __exit__(self, exc_type, exc_value, traceback) -> None:

        if exc_type is None:
            _urm.pushEndMark(self.desc)
        else:
            pass
            # TBD - rollback?
        _urm.insideContext = False

    def recordAction(self, function: Callable, *args, **kwargs) -> None:
        _urm.pushAction(function, *args, **kwargs)

# Private Implementation

# The UndoRedoManager class does most of the work
class _UndoRedoManager:

    class Action:
        def __init__(self, function: Callable, *args: str, **kwargs: int) -> None:
            # Store a function with all info needed to execute it later
            self.function = function
            self.args = args
            self.kwargs = kwargs
        def execute(self) -> Any:
            # Execute the stored function with its arguments
            return self.function(*self.args, **self.kwargs)
        def dump(self) -> None:
            # Just for debugging
            print(self.function, self.args, self.kwargs)

    class Mode(Enum):
        # This enum is used to describe what we are doing at the moment
        DOING = 1,
        UNDOING = 2,
        REDOING = 3

    def __init__(self) -> None:
        # Used to detect nested contexts
        self.insideContext = False
        # Used to determine if any actions were pushed during undo/redo
        self.actions_pushed = False
        self.reset()

    def reset(self) -> None:
        # The two stacks
        self.undo_stack: list[_UndoRedoManager.Action] = []
        self.redo_stack: list[_UndoRedoManager.Action] = []
        # Current mode
        self.mode = _UndoRedoManager.Mode.DOING

    def pushAction(self, function: Callable, *args, **kwargs) -> None:
        action = _UndoRedoManager.Action(function, *args, **kwargs)
        # When pushing an Action, different things happen depending what we are doing
        if self.mode == _UndoRedoManager.Mode.DOING:
            if not self.insideContext:
                raise RuntimeError('UndoRedoManager: pushAction outside UndoContext')
            if self.redo_stack != []:
                self.redo_stack.clear()
            self.undo_stack.append(action)
        elif self.mode == _UndoRedoManager.Mode.UNDOING:
            self.redo_stack.append(action)
            self.actions_pushed = True
        elif self.mode == _UndoRedoManager.Mode.REDOING:
            self.undo_stack.append(action)
            self.actions_pushed = True

    def pushEndMark(self, desc = "Undescribed") -> None:
        # We only allow pushing end marks here in DOING mode
        # End marks during UNDOING or REDOING happen via direct calls to pushAction()
        if self.mode == _UndoRedoManager.Mode.DOING:
            if self.undo_stack != []:
                if self.undo_stack[-1].function == self.endMarkFunction:
                    raise RuntimeError('UndoRedoManager: pushEndMark without Action(s)')
            self.pushAction(self.endMarkFunction, desc)
            
    def endMarkFunction(self, desc: str) -> None:
        # This is a placeholder function - it does nothing
        # but it does contain the description of the action group as args[0]
        pass

    # Note: Undo and Redo are the same code, except for the mode and the stacks involved
    def undoOrRedo(self, opname: str, mode: Mode, stack: list[_UndoRedoManager.Action]) -> str:
        # Set the mode to UNDOING or REDOING
        self.mode = mode
        if stack != []:
            # The top of the stack should always be an endMarkFunction
            endaction = stack.pop()
            if endaction.function != self.endMarkFunction: # this shouldn't happen
                msg = f'UndoRedoManager: {opname}ing without Mark!'
                raise RuntimeError(msg)
            # Extract the description of the action group
            desc = endaction.args[0]
            # Now execute actions until we hit the next endMarkFunction
            # and track if any new actions are pushed during the process
            self.actions_pushed = False
            done = False
            while not done:
                if stack == []: # this shouldn't happen
                    msg = f'UndoRedoManager: {opname}ing with no Action!'
                    raise RuntimeError(msg)
                if stack[-1].function == self.endMarkFunction:
                    done = True
                else:
                    # Execute the next action
                    stack.pop().execute()
                    if stack == []:
                        done = True
            # If any actions were pushed during the undo/redo,
            # We push a new endMarkFunction to mark the end of the group
            # and return the description
            if self.actions_pushed:
                self.pushAction(self.endMarkFunction, desc)
            rv = desc
        else:
            # If there is nothing to undo/redo, return empty string
            rv = ''
        # Put the mode back to DOING
        self.mode = _UndoRedoManager.Mode.DOING
        return rv

    def dumpStacks(self) -> None:
        # This is just for debugging
        print("Undo Stack:")
        for action in self.undo_stack:
            action.dump()
        print("Redo Stack:")
        for action in self.redo_stack:
            action.dump()

# One and only one UndoRedoManager
_urm = _UndoRedoManager()

# Test code
def testUndoRedo() -> None:

    def undoFunction(uctx, msg: str) -> None:
        print("    Undo Function")
        uctx.recordAction(redoFunction, uctx, msg)

    def redoFunction(uctx, msg: str) -> None:
        print("    Redo Function")
        uctx.recordAction(undoFunction, uctx, msg)

    def test_undo() -> None:
        s = undo()
        print(f'Undone {s if s != "" else "nothing"}')

    def test_redo() -> None:
        s = redo()
        print(f'Redone {s if s != "" else "nothing"}')

    print("Doing some actions...")

    #a = 1
    with undoContext("Action 1") as uctx:
        uctx.recordAction(undoFunction, uctx, "Action 1")
        print("Doing action 1")
        #a = uctx
    #a.recordAction(undoMessage, a, "Action 1a")
    #print("Doing action 1a")
    with undoContext("Actions 2 and 3") as uctx:
        uctx.recordAction(undoFunction, uctx, "Action 2")
        uctx.recordAction(undoFunction, uctx, "Action 3")
        print("Doing actions 2 & 3")
    with undoContext("Action 4") as uctx:
        uctx.recordAction(undoFunction, uctx, "Action 4")
        print("Doing action 4")

    test_undo() # undo action 4
    test_undo() # undo action 2 & 3
    test_redo() # redo action 2 & 3

    with undoContext("Actions 5") as uctx:
        uctx.recordAction(undoFunction, uctx, "Action 5")
        print("Doing action 5")

    test_undo() # undo action 5
    test_undo() # undo action 2 & 3
    test_undo() # undo action 1
    test_undo() # nothing to undo

    test_redo() # undo action 1
    test_redo() # redo action 2 & 3
    test_redo() # redo action 5
    test_redo() # nothing to redo

if __name__ == '__main__':
    testUndoRedo()

