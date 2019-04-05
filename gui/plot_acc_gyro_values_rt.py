from bluepy import btle
from struct import *
import binascii
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.animation as animation

acc_UUID='340a1b80-cf4b-11e1-ac36-0002a5d5c51b'
gyr_UUID='02f7090f-cf8a-11e1-dca9-0002a5d5c51b'

print ("Connecting...")
dev = btle.Peripheral("C0:9f:e4:80:c9:23", btle.ADDR_TYPE_RANDOM)
 
print ("Services...")
for svc in dev.services:
    print (str(svc))

service=dev.getServiceByUUID('02366e80-cf3a-11e1-9ab4-0002a5d5c51b')

print ("Characteristics...")
acc_char=service.getCharacteristics(acc_UUID)[0]
gyr_char=service.getCharacteristics(gyr_UUID)[0]

# Plotting
# Parameters
x_len = 300         # Number of points to display
y_acc_range = [-2000, 2000]  # Range of possible Y values to display for acc
y_gyr_range = [-10000, 10000]  # Range of possible Y values to display for gyr

# Create figure for plotting
fig, ((ax1, ax4), (ax2, ax5), (ax3, ax6))= plt.subplots(3,2)

ax1.set_ylim(y_acc_range)
ax1.set_ylabel('Acceleration X')
ax1.set_title('Acceleration Data')

ax2.set_ylim(y_acc_range)
ax2.set_ylabel('Acceleration Y')

ax3.set_ylim(y_acc_range)
ax3.set_ylabel('Acceleration Z')
ax3.set_xlabel('Showing the last 300 samples')

ax4.set_ylim(y_gyr_range)
ax4.set_ylabel('Angle X')
ax4.set_title('Gyroscope Data')

ax5.set_ylim(y_gyr_range)
ax5.set_ylabel('Angle Y')

ax6.set_ylim(y_gyr_range)
ax6.set_ylabel('Angle Z')
ax6.set_xlabel('Showing the last 300 samples')

xs = list(range(0, x_len))
ys1 = [0] * x_len
ys2 = [0] * x_len
ys3 = [0] * x_len
ys4 = [0] * x_len
ys5 = [0] * x_len
ys6 = [0] * x_len

fig.align_labels()

# Create a blank line. We will update the line in animate
line1, = ax1.plot(xs, ys1)
line2, = ax2.plot(xs, ys2)
line3, = ax3.plot(xs, ys3)
line4, = ax4.plot(xs, ys4)
line5, = ax5.plot(xs, ys5)
line6, = ax6.plot(xs, ys6)
line=[line1, line2, line3, line4, line5, line6]

# This function is called periodically from FuncAnimation
def animate(i, ys1, ys2, ys3, ys4, ys5, ys6):

    # Read acceleration and gyroscope values from LSM6DS3
    acc_packed=acc_char.read()
    acc_unpacked=unpack('hhh', acc_packed)
    gyr_packed=gyr_char.read()
    gyr_unpacked=unpack('hhh', gyr_packed)

    # Retrieving values
    acc_x=acc_unpacked[0]
    acc_y=acc_unpacked[1]
    acc_z=acc_unpacked[2]
    gyr_x=gyr_unpacked[0]
    gyr_y=gyr_unpacked[1]
    gyr_z=gyr_unpacked[2]
    
    # Adding values to the axis
    ys1.append(acc_x)
    ys2.append(acc_y)
    ys3.append(acc_z)
    ys4.append(gyr_x)
    ys5.append(gyr_y)
    ys6.append(gyr_z)


    # Limit y list to set number of items
    ys1 = ys1[-x_len:]
    ys2 = ys2[-x_len:]
    ys3 = ys3[-x_len:]
    ys4 = ys4[-x_len:]
    ys5 = ys5[-x_len:]
    ys6 = ys6[-x_len:]

    # Update line with new Y values
    line[0].set_ydata(ys1)
    line[1].set_ydata(ys2)
    line[2].set_ydata(ys3)
    line[3].set_ydata(ys4)
    line[4].set_ydata(ys5)
    line[5].set_ydata(ys6)

    return line

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig,
    animate,
    fargs=(ys1, ys2, ys3, ys4, ys5, ys6),
    interval=350,  #Maxium display rate is 3.3Hz
    blit=True)
plt.show()

##while True:
##    val_packed=char.read()
##    val_unpacked=unpack('hhh', val_packed)
##    print (val_unpacked)

