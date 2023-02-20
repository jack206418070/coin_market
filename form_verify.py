class Fverify:
  def __init__(self, form):
    self.form = form
  def register(self):
    result = {}
    form_arr = ['account', 'password', 'resetPassword', 'name', 'bankName', 'bankAccount']
    for el in form_arr:
      if el in self.form:
        result['stauts'] = True
      else:
        result['stauts'] = False
        result['error'] = f'{el}為必填欄位'
        return result
    if form_arr['password'] != form_arr['resetPassword']:
      result['stauts'] = False
      result['error'] = '驗證密碼必須與密碼欄位一樣'
      return
    return result