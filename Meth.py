from pyrogram import Client, filters
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from io import BytesIO
import numexpr as ne

def add_on_commands(app: Client):
    @app.on_message(filters.command("math", prefixes="."))
    def math_command(client, message):
        try:
            expression = message.text.split(' ', 1)[1]
            result = ne.evaluate(expression)
            if result == 300:
                message.reply_photo(photo='NOPE.jpg')
            else:
                message.reply_text(f"{result}")
        except IndexError:
            message.reply_text("Please provide a valid mathematical expression.")
        except ne.NumExprError:
            message.reply_text("There was an error evaluating the expression. Please check your input.")
        except Exception as e:
            message.reply_text(f"An unexpected error occurred: {e}")

    @app.on_message(filters.command("plot", prefixes="."))
    def plot_command(client, message):
        try:
            data = message.text.split(' ', 1)[1]
            points = list(map(float, data.split()))
            x_coords = points[0::2]
            y_coords = points[1::2]
            plt.plot(x_coords, y_coords, marker='o')
            plt.title("Plot")
            plt.xlabel("x")
            plt.ylabel("y")
            plt.grid(True)
            plt.axis('equal')
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            message.reply_photo(photo=buf)
            plt.close()
        except (ValueError, IndexError):
            message.reply_text("Please provide valid numbers in the format x1 y1 x2 y2 ...")
        except Exception as e:
            message.reply_text(f"An unexpected error occurred: {e}")
