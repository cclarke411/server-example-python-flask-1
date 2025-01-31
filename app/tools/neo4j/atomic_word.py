from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Function to generate a word cloud from a text file
def generate_wordcloud(file_path):
    try:
        # Read the contents of the file
        with open(file_path, 'r') as file:
            text = file.read()

        # Generate the word cloud
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)

        # Display the word cloud using Matplotlib
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.show()

    except FileNotFoundError:
        print(f"The file {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage (replace 'sample.txt' with your actual file path)
if __name__ == "__main__":
    filepath = "/Users/clydeclarke/Documents/server-example-python-flask/data/atomic_habits.txt"
    generate_wordcloud(filepath)
