class TokenProcessor:
    _assign = 'assign'
    _korv = 'korv'
    _obj_begin = 'obj_begin'
    _obj = 'obj'

    def __init__(self, tokens):
        self.tokens = tokens
        self.ver = self.tokens[0]
        self._vaildate()

    def _vaildate(self):
        assert self.tokens[1] == ':'
        assert self.tokens[2] == '{'
        assert self.tokens[-1] == '}'

    def _append(self, token):
        self.stack.append(token)
        p = self._korv
        if isinstance(token, dict):
            p = self._obj
        elif token == '{':
            p = self._obj_begin
        elif token == '=':
            p = self._assign
        self.process.append(p)

    def _pop_process(self, n):
        for i in range(n):
            self.process.pop()

    def _create_item(self):
        self._pop_process(2)  # popout _assign and _korv
        self.stack.pop()  # popout =
        k = self.stack.pop()  # popout korv
        self._append({k: {}})  # re-insert as item

    def _process_sep(self):
        lp = self.process[-1]
        if lp == self._korv:
            v = self.stack.pop()
            _ = self.stack.pop()
            k = self.stack.pop()
            self._pop_process(3)
            self._append({k:v})

    def _process_deep_obj(self):
        kv = {}
        lp = self.process.pop()
        while lp == self._obj:
            cur = self.stack.pop()
            kv.update(cur)
            # for k, v in cur.items():
            #     kv[k] = v
            lp = self.process.pop()
        # process while found _obj_begin
        self.stack.pop()  # popout {
        # print('kv:', kv)
        # there are 2 deep obj
        # 1. {k = {k2 = {}}} -> assign to key
        # 2. {{}, {}, {}} -> insert as obj
        if self.process and self.process[-1] == self._assign:
            # 1st deep obj form
            self._pop_process(2)  # popout _assign and _korv
            self.stack.pop()  # popout =
            k = self.stack.pop()  # popout korv
            self._append({k: kv})
        else:
            # 2nd deep obj form
            self._append(kv)


    def _process_obj_end(self):
        lp = self.process[-1]
        if lp == self._obj_begin:
            # process {} as item
            item = {}
            self.stack.pop()  # popout {
            self.process.pop()  # popout _obj_begin
            # ensure if this is assignment
            lp = self.process[-1]
            if lp == self._assign:
                self._create_item()
        elif lp == self._obj:
            # end of deep {k = {k1 = {}, k2 = {}}}
            self._process_deep_obj()
        elif lp == self._korv:
            # end of deep {..., k = v}
            self._pop_process(3)  # popout _korv, _assign, _korv
            v = self.stack.pop()
            _ = self.stack.pop()
            k = self.stack.pop()
            self._append({k: v})
            self._process_deep_obj()

    def _generate_output(self):
        res = []
        for s in self.stack:
            if 'param2' not in s:
                res.append(dict(**s, **{'param2': '0'}))
            else:
                res.append(s)
        return res

    def process_token(self):
        self.stack = []
        self.process = []
        for token in self.tokens[3:-1]:
            # print('processing', token)
            if token == '{':
                self._append(token)
            elif token == '}':
                self._process_obj_end()
            elif token == '=':
                self._append(token)
            elif token == ',':
                self._process_sep()
            else:  # key or value
                self._append(token)
        return self._generate_output()
