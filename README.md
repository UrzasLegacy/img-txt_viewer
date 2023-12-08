# img-txt_viewer
Display an image and text file side-by-side for easy manual captioning. + Tons of features to help you work faster!

![v1 74_img-txt_viewer](https://github.com/Nenotriple/img-txt_viewer/assets/70049990/7949c61d-c507-4dd2-934c-906feef3b9fe)

# 📝 Usage

- Prepare Your Files:
  - Put each image and its matching text file in the same folder.
  - If you choose to include a text pair for an image, ensure they are located in the same folder and have identical names.
  - For example: `01.png` and `01.txt`, `02.jpg` and `02.txt`...
  - Supported image types: `.png` `.jpg` `.jpeg` `.jfif` `.jpg_large` `.webp` `.bmp`


# 💡 Tips and Features

- Shortcuts:
  - `ALT+Left/Right`: Quickly move between img-txt pairs.
  - `Del`: Send the current pair to a local trash folder.
  - `ALT`: Cycle through auto-suggestions.
  - `TAB`: Insert the highlighted suggestion.
  - `CTRL+F`: Highlight all duplicate words. 
  - `CTRL+S`: Save the current text file.
  - `CTRL+Z` / `CTRL+Y`: Undo/Redo.
  - `Middle-click`: a token to quickly delete it.

- Tips:
  - `Highlight duplicates` by selecting text.
  - Enable `List View` to display text in a vertical list format.
  - Enable `Big Comma Mode` for more visual separation between captions.
  - Blank text files can be created for images without any matching files when loading a directory.
  - `Autocomplete Suggestions` while you type using Danbooru/Anime tags, the English Dictionary, or both. 
  - `Fuzzy Search` Use an asterisk * while typing to return a broader range of suggestions.
    - For example: Typing `*lo*b` returns "<ins>**lo**</ins>oking <ins>**b**</ins>ack", and even "yel<ins>**lo**</ins>w <ins>**b**</ins>ackground"

- Text Tools:
  - `Batch Token Delete`: View all tokens in a directory as a list, and quickly delete them.
  - `Cleanup Text`: Fix simple typos in all text files of the selected folder.
  - `Prefix Text Files`: Insert text at the START of all text files.
  - `Append Text Files`: Insert text at the END of all text files.
  - `Search and Replace`: Edit all text files at once.

 - Auto-Save
   - Check the auto-save box to save text when navigating between img/txt pairs or closing the window.
   - Text is cleaned when saved, so you can ignore typos such as duplicate tokens, multiple spaces or commas, missing spaces, and more.
   - `Clean text on save` Can be disabled from the options menu. *(Disabling this may have adverse effects when inserting a suggestion)*

# 🚩 Requirements

You don't need to worry about anything if you're using the [portable/executable](https://github.com/Nenotriple/img-txt_viewer/releases?q=executable&expanded=true) version.

___

You must have **Python 3.10+** installed to the system PATH.

**Running the script will automatically fulfill all requirements.**

The `pillow` library will be downloaded and installed *(if not already available)* upon launch.

`dictionary.csv` `danbooru.csv` `e621.csv` will be downloaded *(if not already available)* upon launch.

# 📜 Version History

[v1.82 changes:](https://github.com/Nenotriple/img-txt_viewer/releases/tag/v1.82)

The biggest visible change this release is the addition of a new Paned Window that now holds all text tools. (excluding Batch Tag Delete)
This makes it way more simple and easier to use these tools.

  - New:
    - Search and Replace, Prefix Text, Append Text, Font Options, and Edit Custom Dictionary are now in a convient tabbed interface below the text box.
    - You can now refresh the custom dictionary

<br>

  - Fixed:
    - Saving a blank text file now deletes it.
    - Fixed error when 'Cleanup Text' was run in a folder where some images had missing text pairs.
    - Fixed an error when attempting to delete an img-txt pair and no text file was present.
    - 'Batch Tag Delete' and 'About' no longer open beside the main window. This prevents the new window from opening off the screen.
    - Running 'Prefix' or 'Append' text now creates text files for images that previously didn't have a pair.

<br>

  - Other changes:
    - Basically all text tools were completly redone.
    - I've tried to fix as many small bugs and add polish wherever possible. Too many changes to list them all.
