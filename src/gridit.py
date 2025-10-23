import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
#from tkinter.simpledialog import askfloat
from PIL import Image, ImageTk
import math
import asyncio
from pynnex import with_emitters, emitter, listener
from solver2 import NLLSSolver
from undoredo import UndoRedoAction, UndoRedoManager

def print_hierarchy(widget, indent=0):
    """Prints the widget hierarchy starting from the given widget."""
    print(" " * indent + widget.winfo_class() + " " + str(widget))
    for child in widget.winfo_children():
        print_hierarchy(child, indent + 2)

class AutoScrollbar(ttk.Scrollbar):
    """ A scrollbar that hides itself if it's not needed. Works only for grid geometry manager """
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

'''
class ConstraintGUI:
    def __init__(self, id):
        self.id = id
    def setConstraint(self, c):
        self.c = c
    def getConstraint(self, c):
        return c
'''

class Marker:
    next_marker_id = 0
    def __init__(self, image_x, image_y, id=id, mtype = 0):
        if id == None:
            self.id = Marker.next_marker_id
        else:
            self.id = id
        Marker.next_marker_id += 1
        self.mtype = mtype
        self.image_x = image_x
        self.image_y = image_y
        self.prehighlighted = False
        self.selected = False
        self.xconstraints = []
        self.yconstraints = []

class ScrollableImageFrame(ttk.Frame):
    @listener
    def __init__(self, parent, path, *args, **kwargs):
        super(ScrollableImageFrame, self).__init__(parent, *args, **kwargs)
        
        #s=ttk.Style()
        #s.configure('yellow.TFrame', background='yellow')
        #self.configure(style='yellow.TFrame')

        self.parent = parent
        self.path = path
        self.imscale = 1.0  # scale for the canvas image zoom, public for outer classes
        self.delta = 1.25  # zoom magnitude
        # Initialize Widgets
        # Scrollbars
        hbar = AutoScrollbar(self, orient="horizontal")
        vbar = AutoScrollbar(self, orient="vertical")
        hbar.grid(row=1, column=0, sticky='we')
        vbar.grid(row=0, column=1, sticky='ns')
        # Canvas
        self.canvas = tk.Canvas(self,
                                highlightthickness = 0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        hbar.configure(command=self.scroll_x)
        vbar.configure(command=self.scroll_y)
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', lambda event: self.show_image())  # canvas is resized
        #self.canvas.bind('<ButtonPress-1>', self.createMarker)
        self.canvas.bind('<ButtonPress-2>', self.panBegin)
        self.canvas.bind('<B2-Motion>', self.panEnd)
        self.canvas.bind('<MouseWheel>', self.wheel)  # zoom for Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self.wheel)  # zoom for Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self.wheel)  # zoom for Linux, wheel scroll up
        self.canvas.bind('<Motion>', self.motion)
        self.canvas.bind('<KeyRelease>', self.key)
        self.canvas.bind('<ButtonPress-3>', self.test)
        self.image = Image.open(path)
        self.imwidth, self.imheight = self.image.size
        self.min_side = min(self.imwidth, self.imheight)
        
        # Create image pyramid
        self.pyramid = [Image.open(self.path)]
        # Set ratio coefficient for image pyramid
        self.ratio = 1.0
        self.curr_img = 0  # current image from the pyramid
        self.scale = self.imscale * self.ratio
        self.reduction = 2  # reduction degree of image pyramid
        (w, h), m, j = self.pyramid[-1].size, 512, 0
        #print(w,h)
        n = math.ceil(math.log(min(w, h) / m, self.reduction)) + 1  # image pyramid length
        while w > m and h > m:  # top pyramid image is around 512 pixels in size
            j += 1
            print('Creating image pyramid: {j} from {n}'.format(j=j, n=n))
            w /= self.reduction  # divide on reduction degree
            h /= self.reduction  # divide on reduction degree
            self.pyramid.append(self.pyramid[-1].resize((int(w), int(h)), Image.LANCZOS))
            print(w,h)
        self.last_imageid = None

        self.markers = {}
        self.undo_redo_manager = UndoRedoManager()
        self.solver = NLLSSolver()
        self.solver.emitcreateconstraint.connect(self, self.on_createconstraint)
        self.solver.emitdestroyconstraint.connect(self, self.on_destroyconstraint)

        # These came from GIMP
        #self.scales = [1.5,2.0,3.0,4.0,5.5,8.0,11.0,16.0,
        #               23.0,32.0,45.0,64.0,90.0,128.0,180.0,256.0]
        #for scale in self.scales:
        #    iw = int(w/scale)
        #    ih = int(h/scale)
        #    if iw > 0 and ih > 0:
        #        self.pyramid.append(self.pyramid[-1].resize((iw,ih),Image.LANCZOS))
        
        #cc=1
        #for elem in self.pyramid:
        #    elem.save(f'temp{cc}.png')
        #    cc+=1

        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0, tag='rect')
        print(f'self.container = {self.container}')
        self.show_image()
        self.canvas.focus_set()

    def grid(self, **kw):
        """ Put CanvasImage widget on the parent widget """
        super().grid(**kw)  # place CanvasImage widget on the grid
        super().grid(sticky='nswe')  # make frame container sticky
        super().rowconfigure(0, weight=1)  # make canvas expandable
        super().columnconfigure(0, weight=1)

    # noinspection PyUnusedLocal
    def scroll_x(self, *args, **kwargs):
        """ Scroll canvas horizontally and redraw the image """
        self.canvas.xview(*args)  # scroll horizontally
        self.show_image()  # redraw the image

    # noinspection PyUnusedLocal
    def scroll_y(self, *args, **kwargs):
        """ Scroll canvas vertically and redraw the image """
        self.canvas.yview(*args)  # scroll vertically
        self.show_image()  # redraw the image

    def show_image(self):
        box_image = self.canvas.coords(self.container)  # get image area
        box_canvas = (self.canvas.canvasx(0),  # get visible area of the canvas
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        box_img_int = tuple(map(int, box_image))  # convert to integer or it will not work properly
        # Get scroll region box
        box_scroll = [min(box_img_int[0], box_canvas[0]), min(box_img_int[1], box_canvas[1]),
                      max(box_img_int[2], box_canvas[2]), max(box_img_int[3], box_canvas[3])]
        # Horizontal part of the image is in the visible area
        if  box_scroll[0] == box_canvas[0] and box_scroll[2] == box_canvas[2]:
            box_scroll[0]  = box_img_int[0]
            box_scroll[2]  = box_img_int[2]
        # Vertical part of the image is in the visible area
        if  box_scroll[1] == box_canvas[1] and box_scroll[3] == box_canvas[3]:
            box_scroll[1]  = box_img_int[1]
            box_scroll[3]  = box_img_int[3]
        # Convert scroll region to tuple and to integer
        self.canvas.configure(scrollregion=tuple(map(int, box_scroll)))  # set scroll region
        x1 = max(box_canvas[0] - box_image[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(box_canvas[1] - box_image[1], 0)
        x2 = min(box_canvas[2], box_image[2]) - box_image[0]
        y2 = min(box_canvas[3], box_image[3]) - box_image[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            croppedimage = self.pyramid[max(0, self.curr_img)].crop(
                            (int(x1 / self.scale), int(y1 / self.scale),
                             int(x2 / self.scale), int(y2 / self.scale)))
            imagetk = ImageTk.PhotoImage(croppedimage.resize((int(x2 - x1), int(y2 - y1)), Image.LANCZOS))
            imageid = self.canvas.create_image(max(box_canvas[0], box_img_int[0]),
                                               max(box_canvas[1], box_img_int[1]),
                                               anchor='nw', image=imagetk, tag='image')
            self.x1 = x1
            self.y1 = y1
            if self.last_imageid:
                self.canvas.delete(self.last_imageid)
            self.last_imageid = imageid
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

    def motion(self, event):
        if not self.outside(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)):
            x,y = self.canvasToImage((self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)))
            #print(f'x,y: {x},{y}')

    def canvasToImage(self, coords):
        x_offs, y_offs = self.canvas.coords(self.last_imageid)
        x = (coords[0] - x_offs + self.x1)/self.imscale
        y = (coords[1] - y_offs + self.y1)/self.imscale
        return (x,y)
    
    def ImageToCanvas(self, coords):
        x_offs, y_offs = self.canvas.coords(self.last_imageid)
        x = coords[0]*self.imscale + x_offs - self.x1
        y = coords[1]*self.imscale + y_offs - self.y1
        #print(f'pick_c = {x_offs},{y_offs}')
        #print(f'image_c  = {self.x1},{self.y1}')
        #print(f'coords_i = {coords[0]},{coords[1]}') 
        #print(f'scale    = {self.imscale}')
        #print(f'xy_c     = {x},{y}')
        #print()
        return (x,y)
    
    def canvasDump(self):
        all_item_ids = self.canvas.find_all()
        for item_id in all_item_ids:
            item_type = self.canvas.type(item_id)
            tags = self.canvas.gettags(item_id)
            print(f"Item ID: {item_id}, Type: {item_type}, Tags: {tags}")

    def panBegin(self, event):
        """ Remember previous coordinates for scrolling with the mouse """
        self.canvas.scan_mark(event.x, event.y)

    def panEnd(self, event):
        """ Drag (move) canvas to the new position """
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.show_image()  # zoom tile and show it on the canvas

    def outside(self, x, y):
        """ Checks if the point (x,y) is outside the image area """
        bbox = self.canvas.coords(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False  # point (x,y) is inside the image area
        else:
            return True  # point (x,y) is outside the image area
        
    def wheel(self, event):
        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y): return  # zoom only inside image area
        #print(event) #############
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down, zoom out, smaller
            if round(self.min_side * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.delta
            scale        /= self.delta
        if event.num == 4 or event.delta == 120:  # scroll up, zoom in, bigger
            i = float(min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1)
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.delta
            scale        *= self.delta
        # Take appropriate image from the pyramid
        k = self.imscale * self.ratio  # temporary coefficient
        self.curr_img = min((-1) * int(math.log(k, self.reduction)), len(self.pyramid) - 1)
        self.scale = k * math.pow(self.reduction, max(0, self.curr_img))
        #
        print(f'Scaling... {scale}')
        self.canvas.scale('image', x, y, scale, scale)
        self.canvas.scale('rect', x, y, scale, scale)
        self.show_image()
        self.updateMarkers()
        # Redraw some figures before showing image on the screen
        ##self.redraw_figures()  # method for child classes
        self.show_image()

    def updateMarkers(self):
        # move marker items to new locations
        for id in self.markers:
            items = self.canvas.find_withtag(f'C{id}')
            for item in items:
                self.canvas.delete(item)
            self.createMarkerSymbol(self.markers[id])
    
    def createMarkerSymbol(self,marker):
        r = 10
        xc, yc = self.ImageToCanvas([marker.image_x, marker.image_y])
        if marker.mtype == 0:
            self.canvas.create_line(xc-r, yc, xc+r, yc, fill='blue', tags = f'C{marker.id}')
            self.canvas.create_line(xc, yc-r, xc, yc+r, fill='blue', tags = f'C{marker.id}')
            self.canvas.create_oval(xc-r, yc-r, xc+r, yc+r, width=3, outline='blue', tags = f'C{marker.id}')

    def createMarker(self,x,y,id=None):
        marker = Marker(x,y,id)
        self.markers[marker.id] = marker
        self.createMarkerSymbol(marker)
        print(f'Created Marker, id={marker.id}')
        self.undo_redo_manager.pushAction(UndoRedoAction(self.deleteMarker, marker.id))

        #xw = askfloat("X coordinate", "X coordinate?", parent=self)
        #yw = askfloat("Y coordinate", "Y coordinate?", parent=self)
        #c = self.solver.CreateConstraint(x,y,xw,yw,emit=False)
        #T = self.solver.ComputeSolution()
    
    def deleteMarker(self, id):
        marker = self.markers[id]
        id,x,y = marker.id, marker.image_x, marker.image_y
        self.markers.pop(id)
        items = self.canvas.find_withtag(f'C{id}')
        for item in items:
            self.canvas.delete(item)
        print(f'Deleted Marker, id={id}')
        self.undo_redo_manager.pushAction(UndoRedoAction(self.createMarker, x, y, id))

    def on_createconstraint(self,c):
        print('Got create signal')

    def on_destroyconstraint(self,c):
        print('Got destroy signal')

    def key(self, event):
        if event.char == 'm' or event.char == 'M':
            #self.canvasDump()
            if self.outside(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)):
                return
            x,y = self.canvasToImage((self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)))
            self.createMarker(x,y)
        elif event.char == 'z':
            self.undo_redo_manager.undo()
        elif event.char == 'y':
            self.undo_redo_manager.redo()
        #print(event)

    def test(self, event):
        self.updateMarkers()
        self.show_image()

class App(ttk.Frame):
    def __init__(self):
        # main setup
        super().__init__(master=tk.Tk())

        ### create instances
        self.imframe = None

        ### create main window
        self.master.title('Gridit')
        self.master.geometry('800x600+0+0')
        self.master.protocol('WM_DELETE_WINDOW', self.destroy)
        # various binds here

        ### create widgets

        # Create Menubar
        self.menubar = tk.Menu(self.master)
        # Create File Menu
        #self.__file = tk.Menu(self.menubar, tearoff=False, postcommand=self.__list_recent)
        self.__file = tk.Menu(self.menubar, tearoff=False)
        self.__file.add_command(label='Open image',
                                command=self.open_image,
                                accelerator='Ctrl+O')
        self.__file.add_separator()
        self.__file.add_command(label='Print Hierarchy',
                                command=lambda: print_hierarchy(self.master),
                                accelerator='Ctrl+P')
        self.__file.add_separator()
        self.__file.add_command(label='Exit',
                                command=self.destroy,
                                accelerator=u'Alt+F4')
        self.menubar.add_cascade(label='File', menu=self.__file)

        # Add menubar to the master frame
        self.master.configure(menu=self.menubar)

        self.master.rowconfigure(0, weight=1)  # make grid cell expandable
        self.master.columnconfigure(0, weight=1)
        
        self.placeholder = ttk.Frame(self.master)
        self.placeholder.grid(row=0, column=0, sticky='nswe')
        self.placeholder.rowconfigure(0, weight=1)  # make grid cell expandable
        self.placeholder.columnconfigure(0, weight=1)

        #s = ttk.Style()
        #s.configure('blue.TFrame', background='blue')
        #self.placeholder.config(style='blue.TFrame')

        # for now
        #self.set_image('imagetest1.png')
        #self.set_image('imagetest2.png')
        #self.set_image('imagetest3.png')

        #print_hierarchy(self)

        # run
        self.mainloop()

    def set_image(self, path):
        """ Close previous image and set a new one """
        self.close_image()  # close previous image
        self.imframe = ScrollableImageFrame(self.placeholder, path=path)  # create image frame
        self.imframe.grid()

    def open_image(self):
        """ Open image in the GUI """
        path = askopenfilename(title='Select an image')
        if path == '': return
        self.set_image(path)

    def close_image(self):
        """ Close image """
        if self.imframe:
            self.imframe.destroy()
            self.imframe = None

    def destroy(self):
        """ Destroy the main frame object and release all resources """
        self.close_image()
        self.quit()

async def main():
    App()

if __name__ == '__main__':
    asyncio.run(main())  # start the application
