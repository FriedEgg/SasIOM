import sublime, sublime_plugin, subprocess, os, re, Pywin32.setup
import win32com.client

class SasiomCommand(sublime_plugin.WindowCommand):
  def run(self):
    self.window.active_view().run_command('save')
    source2 = self.window.active_view().file_name()
    ext = os.path.splitext(source2)[-1].lower()
    if ext == '.sas':
      with open(source2,'r') as saspgm:
          program = saspgm.readlines()
      log_filename = source2[:-3] + 'log'
      if os.path.exists(log_filename):
          os.remove(log_filename)
      lst_filename = source2[:-3] + 'lst'
      if os.path.exists(lst_filename):
          os.remove(lst_filename)
      s = sublime.load_settings( 'sas.sublime-settings' )
      iomsrv = s.get( 'serverinfo_xml' , 'C:/Users/' + os.getenv('USERNAME') + '/AppData/Roaming/SAS/MetadataServer/oms_serverinfo2.xml' )
      iomusr = s.get( 'userinfo_xml'   , 'C:/Users/' + os.getenv('USERNAME') + '/AppData/Roaming/SAS/MetadataServer/oms_userinfo2.xml'   )
      iomcon = s.get( 'server_logical_name' , 'SASApp - Logical Workspace Server' )
      objFactory = win32com.client.Dispatch( 'SASObjectManager.ObjectFactoryMulti2' )
      objFactory.SetMetadataFile( iomsrv , iomusr , False )
      objSAS = objFactory.CreateObjectByLogicalName( iomcon , '' )
      objSAS.LanguageService.Submit( ' '.join(program) )
      list = "foo"
      while list != "":
          list = objSAS.LanguageService.FlushList(1000)
          with open(lst_filename,'a') as lst_file:
              lst_file.write(list)
      log = "foo"
      while log != "":
          log = objSAS.LanguageService.FlushLog(1000)
          with open(log_filename,'a') as log_file:
              log_file.write(log)
      objSAS.Close()
      if os.path.exists(lst_filename):
        self.window.open_file( lst_filename )
      if os.path.exists(log_filename):
        self.window.open_file( log_filename )
    else:
      sublime.mesage_dialog('Sorry, this only works with .sas files.')