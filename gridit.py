import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageTk
import math

"""
class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        <create the rest of your GUI here>

if __name__ == "__main__":
    root = tk.Tk()
    MainApplication(root).pack(side="top", fill="both", expand=True)
    root.mainloop()
"""

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

class ScrollableImageFrame(ttk.Frame):
    def __init__(self, parent, path, *args, **kwargs):
        super(ScrollableImageFrame, self).__init__(parent, *args, **kwargs)
        
        #s=ttk.Style()
        #s.configure('yellow.TFrame', background='yellow')
        #self.configure(style='yellow.TFrame')

        self.parent = parent
        self.path = path
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
        self.canvas.bind('<ButtonPress-2>', self.panBegin)
        self.canvas.bind('<B2-Motion>', self.panEnd)
        self.canvas.bind('<MouseWheel>', self.wheel)  # zoom for Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self.wheel)  # zoom for Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self.wheel)  # zoom for Linux, wheel scroll up
        self.canvas.bind('<Motion>', self.motion)
        self.image = Image.open(path)
        self.imwidth, self.imheight = self.image.size
        #self.min_side = min(self.imwidth, self.imheight)
        
        # Create image pyramid
        self.pyramid = [Image.open(self.path)]
        # Set ratio coefficient for image pyramid
        self.ratio = 1.0
        self.curr_img = 0  # current image from the pyramid
        (w, h) = self.pyramid[-1].size
        # These came from GIMP
        self.scales = [1.5,2.0,3.0,4.0,5.5,8.0,11.0,16.0,
                       23.0,32.0,45.0,64.0,90.0,128.0,180.0,256.0]
        for scale in self.scales:
            iw = int(w/scale)
            ih = int(h/scale)
            if iw > 0 and ih > 0:
                self.pyramid.append(self.pyramid[-1].resize((iw,ih),Image.LANCZOS))
        
        #cc=1
        #for elem in self.pyramid:
        #    elem.save(f'temp{cc}.png')
        #    cc+=1

        # Put image into container rectangle and use it to set proper coordinates to the image
        self.container = self.canvas.create_rectangle((0, 0, self.imwidth, self.imheight), width=0)
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
            croppedimage = self.pyramid[0].crop(
                            (int(x1 / 1), int(y1 / 1),
                             int(x2 / 1), int(y2 / 1)))
            imagetk = ImageTk.PhotoImage(croppedimage)
            imageid = self.canvas.create_image(max(box_canvas[0], box_img_int[0]),
                                               max(box_canvas[1], box_img_int[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection

    def motion(self, event):
        if not self.outside(self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)):
            print(f'{self.canvas.canvasx(event.x)} {self.canvas.canvasy(event.y)}' )

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
        return
        x = self.canvas.canvasx(event.x)  # get coordinates of the event on the canvas
        y = self.canvas.canvasy(event.y)
        if self.outside(x, y): return  # zoom only inside image area
        print(event) #############
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.num == 5 or event.delta == -120:  # scroll down, zoom out, smaller
            if round(self.__min_side * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.__delta
            scale        /= self.__delta
        if event.num == 4 or event.delta == 120:  # scroll up, zoom in, bigger
            i = float(min(self.canvas.winfo_width(), self.canvas.winfo_height()) >> 1)
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.__delta
            scale        *= self.__delta
        # Take appropriate image from the pyramid
        k = self.imscale * self.__ratio  # temporary coefficient
        self.__curr_img = min((-1) * int(math.log(k, self.__reduction)), len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction, max(0, self.__curr_img))
        #
        self.canvas.scale('all', x, y, scale, scale)  # rescale all objects
        # Redraw some figures before showing image on the screen
        ##self.redraw_figures()  # method for child classes
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

if __name__ == '__main__':
    App()  # start the application
