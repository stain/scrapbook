import maildir

folders = maildir.SubFolder('/home/stain/Maildir')

folder_list = folders.folder_list()

folder = folders.get_folder(folder_list[0])


