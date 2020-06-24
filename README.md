# gizonde
firmware and max patch for controlling winterbloom sol

In order to use this with Ableton and the Winterbloom Sol you will need to do the following steps:

1) replace the `code.py` file on the CIRCUITPY volume that appears when you plug Sol into your computer with `sol/code.py`
2) copy `max4live/gizonde.amxd` and `max4live/bpatcher` into a directory that ableton knows about (note they should be in the same directory)
3) create a midi track in ableton live and send midi out to the `Sol Audio` midi interface
4) add the `gizonde.amxd` file to the midi track you created in step 3

You should now be able to switch between key tracking and envelope modes for the CV outs and 'note on/off' or midi clock modes for the gate outs.
