"""
########################################
#                                      #
#           Tkinter ToolTips           #
#                                      #
#   Version : v1.04                    #
#   Author  : github.com/Nenotriple    #
#                                      #
########################################

Description:
-------------
This script provides a simple way to add tooltips to any tkinter widget.
It allows customization of the tooltip's text, delay, position, state, and style.

"""

import time
from tkinter import Toplevel, Label


class TkToolTip:
    """
    Create a tooltip for any tkinter widget.

    Widget Attributes
    -----------------
    widget : widget
        The tkinter widget to which the tooltip is attached.

    text : str
        The text displayed when the tooltip is shown.

    delay : int
        The delay (in ms) before the tooltip is shown.

    padx : int
        The x-coordinate offset of the tooltip from the pointer.

    pady : int
        The y-coordinate offset of the tooltip from the pointer.

    ipadx : int
        The horizontal internal padding of the tooltip.

    ipady : int
        The vertical internal padding of the tooltip.

    state : str
        Set the visible state of the tooltip

    bg : str
        Background color of the tooltip.

    fg : str
        Foreground (text) color of the tooltip.

    font : tuple
        Font of the tooltip text.

    borderwidth : int
        Border width of the tooltip.

    relief : str
        Border style of the tooltip.

    Other Attributes
    ----------------

    tip_window : Toplevel
        The Toplevel window used to display the tooltip.

    widget_id : int
        The id returned by the widget's `after` method.

    hide_id : int
        The id returned by the widget's `after` method for hiding the tooltip.

    hide_time : float
        The time when the tooltip was hidden.

    """

    def __init__(self, widget, text="", delay=0, padx=0, pady=0, ipadx=0, ipady=0, state=None,
                 bg="#ffffe0", fg="black", font=("TkDefaultFont", "8", "normal"), borderwidth=1, relief="solid"):
        """
        Initialize the tooltip with the given parameters.
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.padx = padx
        self.pady = pady
        self.ipadx = ipadx
        self.ipady = ipady
        self.state = state
        self.bg = bg
        self.fg = fg
        self.font = font
        self.borderwidth = borderwidth
        self.relief = relief

        self.tip_window = None  # The window that displays the tooltip; None when no tooltip is shown
        self.widget_id = None  # ID for the scheduled tooltip display event; None if no event is scheduled
        self.hide_id = None  # ID for the scheduled tooltip hide event; None if no event is scheduled
        self.hide_time = None  # Timestamp of the last time the tooltip was hidden; None if never hidden

        self._bind_widget()

    def _bind_widget(self):
        """Setup event bindings for the widget."""
        self.widget.bind('<Enter>', self._enter, add="+")
        self.widget.bind('<Leave>', self._leave, add="+")
        self.widget.bind('<Motion>', self._motion, add="+")
        self.widget.bind("<Button-1>", self._leave, add="+")
        self.widget.bind('<B1-Motion>', self._leave, add="+")

    def _enter(self, event):
        """Schedule tooltip display after the specified delay."""
        self._schedule_show_tip(event)

    def _leave(self, event):
        """Hide the tooltip and cancel any scheduled events."""
        self._cancel_tip()
        self._hide_tip()

    def _motion(self, event):
        """Reschedule the tooltip display when the cursor moves within the widget."""
        self._schedule_show_tip(event)

    def _schedule_show_tip(self, event):
        """Schedule the tooltip to be shown after the specified delay."""
        if self.widget_id:
            self.widget.after_cancel(self.widget_id)
        self.widget_id = self.widget.after(self.delay, lambda: self._show_tip(event))

    def _show_tip(self, event):
        """Display the tooltip at the specified position."""
        if self.state == "disabled":
            return
        x = event.x_root + self.padx
        y = event.y_root + self.pady
        self._create_tip_window(x, y)

    def _create_tip_window(self, x, y):
        """Create and display the tooltip window."""
        if self.tip_window or not self.text:
            return
        self.tip_window = Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")
        label = Label(self.tip_window, text=self.text, background=self.bg, foreground=self.fg,
                      font=self.font, relief=self.relief, borderwidth=self.borderwidth)
        label.pack(ipadx=self.ipadx, ipady=self.ipady)

    def _hide_tip(self):
        """Destroy the tooltip window if it exists."""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None
            self.hide_time = time.time()

    def _cancel_tip(self):
        """Cancel the scheduled display of the tooltip."""
        if self.widget_id:
            self.widget.after_cancel(self.widget_id)
            self.widget_id = None

    def config(self, text=None, delay=None, padx=None, pady=None, ipadx=None, ipady=None, state=None,
               bg=None, fg=None, font=None, borderwidth=None, relief=None):
        """
        Update the tooltip configuration with the given parameters.
        """
        if text is not None:
            self.text = text
        if delay is not None:
            self.delay = delay
        if padx is not None:
            self.padx = padx
        if pady is not None:
            self.pady = pady
        if ipadx is not None:
            self.ipadx = ipadx
        if ipady is not None:
            self.ipady = ipady
        if state is not None:
            assert state in ["normal", "disabled"], "Invalid state"
            self.state = state
        if bg is not None:
            self.bg = bg
        if fg is not None:
            self.fg = fg
        if font is not None:
            self.font = font
        if borderwidth is not None:
            self.borderwidth = borderwidth
        if relief is not None:
            self.relief = relief

    @classmethod
    def create(cls, widget, text="", delay=0, padx=0, pady=0, ipadx=2, ipady=2, state=None,
               bg="#ffffe0", fg="black", font=("tahoma", "8", "normal"), borderwidth=1, relief="solid"):
        """
        Create a tooltip for the specified widget with the given parameters.

        Parameters
        ----------
        widget : tkinter.Widget
            The widget to which the tooltip will be attached.
        text : str, optional
            The text displayed in the tooltip (default is an empty string).
        delay : int, optional
            Delay in milliseconds before showing the tooltip (default is 0).
        padx : int, optional
            Horizontal offset of the tooltip from the cursor (default is 0).
        pady : int, optional
            Vertical offset of the tooltip from the cursor (default is 0).
        ipadx : int, optional
            Horizontal internal padding of the tooltip (default is 2).
        ipady : int, optional
            Vertical internal padding of the tooltip (default is 2).
        state : str, optional
            State of the tooltip; can be "normal" or "disabled" (default is None).
        bg : str, optional
            Background color of the tooltip (default is "#ffffe0").
        fg : str, optional
            Foreground (text) color of the tooltip (default is "black").
        font : tuple, optional
            Font of the tooltip text (default is ("tahoma", "8", "normal")).
        borderwidth : int, optional
            Border width of the tooltip (default is 1).
        relief : str, optional
            Border style of the tooltip (default is "solid").

        Returns
        -------
        Tooltip
            A new instance of the Tooltip class.
        """
        return cls(widget, text, delay, padx, pady, ipadx, ipady, state, bg, fg, font, borderwidth, relief)

#endregion
################################################################################################################################################
#region -  Changelog

'''


v1.04 changes:


  - New:
    - Now supports an ipadx, or ipady value for interior spacing. The default value is 2.

<br>


  - Fixed:
    -


<br>


  - Other changes:
    - x_offset, and y_offset have been renamed to padx, and pady.


'''
#endregion
