import sublime, sublime_plugin, re
import Pywin32.setup
import pythoncom
import win32com.client
import threading
import os

def plugin_loaded():
  global s, Pref
  s = sublime.load_settings('SasIOM.sublime-settings')
  Pref = Pref()
  Pref.load();
  s.add_on_change('reload', lambda:Pref.load())

class Pref:  
  def load(self):
    Pref.connect    = True
    Pref.running    = False
    Pref.err_regx   = re.compile( '(^error:.*$)(^\s{6}\w.*$)*' , re.M + re.I )
    Pref.warn_regx  = re.compile( '(^warning:.*$)(^\s{6}\w.*$)*' , re.M + re.I )
    Pref.program    = ''
    Pref.log        = []
    Pref.error      = []
    Pref.warning    = []
    Pref.lst        = []
    Pref.serverdef  = s.get( 'serverinfo_xml' , 'C:/Users/' + os.getenv('USERNAME') + '/AppData/Roaming/SAS/MetadataServer/oms_serverinfo2.xml' )
    Pref.logindef   = s.get( 'userinfo_xml'   , 'C:/Users/' + os.getenv('USERNAME') + '/AppData/Roaming/SAS/MetadataServer/oms_userinfo2.xml'   )
    Pref.sasapp     = s.get( 'server_logical_name' , 'SASApp - Logical Workspace Server' )
    Pref.objFactory = win32com.client.Dispatch( 'SASObjectManager.ObjectFactoryMulti2' )
    Pref.objFactory.SetMetadataFile( Pref.serverdef , Pref.logindef , False )
    Pref.objSAS     = Pref.objFactory.CreateObjectByLogicalName( Pref.sasapp , '' )

class SasIOMResults:
  def sas_results(self, view):
    view.set_status( 'SasIOM' , "%s" % ( 'SasIOM:///RESULTS' ) )
    self.get_lst(view)
    self.check_log(view)
    status = 'SasIOM:///'
    if len( Pref.err_list ) > 0:
      status += 'ERROR'
    else:
      if len( Pref.warn_list ) > 0:
        status += 'WARNING'
      else:
        status += 'DONE'
    view.set_status( 'SasIOM', "%s" % ( status ) )
    self.output_view = sublime.active_window().get_output_panel("saslist")    
    self.output_view.set_read_only(False)
    self.output_view.run_command('append', {'characters': ''.join( Pref.lst )})
    self.output_view.set_read_only(True)
    sublime.active_window().run_command('show_panel', {'panel': 'output.saslist'})
    Pref.objSAS.Close()

  def check_log(self, view):
    view.set_status( 'SasIOM', "%s" % ( 'SasIOM:///LOG PARSE' ) )
    while 1:
      log_part = Pref.objSAS.LanguageService.FlushLog( 1000 )
      if log_part != '':
        Pref.log.append( log_part )
      else:
        break
    self.log = ''.join( Pref.log )
    Pref.err_list  = re.findall( Pref.err_regx  , self.log )
    Pref.warn_list = re.findall( Pref.warn_regx , self.log )

  def get_lst(self, view):
    view.set_status( 'SasIOM', "%s" % ( 'SasIOM:///GET LST' ) )
    while 1:
      lst_part = Pref.objSAS.LanguageService.FlushList( 1000 )
      if not lst_part == '':
        Pref.lst.append( lst_part )
      else:
        break

class SasiomCommand( sublime_plugin.WindowCommand ):
  def run(self):
    Pref.program = self.window.active_view().substr(sublime.Region(0, self.window.active_view().size()))
    try:
      SasIOMThread( self.window.active_view() ).start()
      #sublime.set_timeout_async( lambda:SasIOMThread( self.window.active_view() ).start(), 0)
    except:
      pass

class SasIOMThread( threading.Thread ):
  def __init__(self, view):
    threading.Thread.__init__(self)
    self.view = view
    status = 'RUNNING'
    self.view.set_status( 'SasIOM', "%s" % ( status ) )

  def run(self):
    Pref.running = True

    try:
      pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)
    except pythoncom.com_error:
      pass

    self.view.set_status( 'SasIOM', "%s" % ( 'SasIOM:///RUNNING' ) )
    Pref.objSAS.LanguageService.Submit( Pref.program )

    sublime.set_timeout(lambda:self.on_done(), 0)

  def on_done(self):
    self.view.set_status( 'SasIOM', "%s" % ( 'SasIOM:///COLLECTING' ) )
    try:
      SasIOMResults().sas_results(self.view)
    except:
      pass
    Pref.running = False