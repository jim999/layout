import layoutController
reload(layoutController)

try:
  controller=layoutController.layoutController()
  controller.start()
except java.lang.Exception as err:
  print("Java exception",traceback.format_exc())
except Exception as err:
  print(traceback.format_exc())
