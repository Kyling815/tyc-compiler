grammar TyC;

options { language=Python3; }

@lexer::header {
from lexererr import *
}

@lexer::members {
# Override emit() to throw the required lexer errors.

def emit(self):
    tk = self.type
    if tk == self.UNCLOSE_STRING:
        result = super().emit()
        raise UncloseString(result.text)
    elif tk == self.ILLEGAL_ESCAPE:
        result = super().emit()
        raise IllegalEscape(result.text)
    elif tk == self.ERROR_CHAR:
        result = super().emit()
        raise ErrorToken(result.text)
    else:
        return super().emit()
}

// =====================
//        PARSER
// =====================

program
    : list_declaration EOF
    ;

list_declaration
    : declaration list_declaration
    | declaration
    ;

declaration
    : struct_declaration
    | function_declaration
    ;

// ----------- STRUCT -----------

struct_declaration
    : STRUCT ID LBRACE list_struct_member? RBRACE SEMI
    ;

list_struct_member
    : struct_member list_struct_member
    | struct_member
    ;

struct_member
    : type_spec ID SEMI
    ;

// ----------- FUNCTION -----------
// chỉ function mới có voidType

function_declaration
    : return_type? ID LPAREN parameter_list? RPAREN block_statement
    ;

return_type
    : VOID
    | type_spec
    ;

parameter_list
    : parameter_decl (COMMA parameter_decl)*
    ;

parameter_decl
    : type_spec ID
    ;

// type_spec KHÔNG có VOID
type_spec
    : INT
    | FLOAT
    | STRING
    | ID
    ;

// ----------- STATEMENTS -----------

list_statement
    : statement list_statement
    | statement
    ;

statement
    : assign_statement SEMI
    | var_statement SEMI
    | if_statement
    | while_statement
    | for_statement
    | switch_statement
    | break_statement
    | continue_statement
    | block_statement
    | expression_statement
    | return_statement
    ;

// accessed must be exactly: ID (DOT ID)*
accessed
    : ID (DOT ID)*
    ;

var_statement
    : (AUTO | type_spec) ID (ASSIGN expression)?
    ;

assign_statement
    : accessed ASSIGN expression
    ;

lvalue
    : accessed
    | lvalue_base (DOT ID)+
    ;

lvalue_base
    : paren_expr
    | struct_literal
    | func_call
    |literal
    ;

func_call
    : ID LPAREN argument_list? RPAREN
    ;

assignment_expr
    : lvalue ASSIGN assignment_expr
    | logical_or_expr
    ;

if_statement
    : IF LPAREN expression RPAREN statement (ELSE statement)?
    ;

while_statement
    : WHILE LPAREN expression RPAREN statement
    ;

// for_update BẮT BUỘC có
for_statement
    : FOR LPAREN for_init? SEMI for_cond? SEMI for_update? RPAREN statement
    ;

for_init
    : var_statement
    | assignment_update
    ;

for_cond
    : expression
    ;

// for update chỉ được: inc/dec hoặc assign
/*for_update
    : incdec_statement
    | assign_statement
    | MINUS lvalue COLON
    ;
*/
for_update
    : assignment_update
    | indec_expr
    | postfix_incdec_any
    | incdec_statement
    ;
// Assignment allowed inside for-update.
assignment_update
    : lvalue ASSIGN assignment_expr
    ;
// bắt buộc có INC/DEC và áp lên lvalue
// hỗ trợ: ++a, a++, ++--a++--, a++--++--
incdec_statement
    : (INC | DEC)+ lvalue (INC | DEC)*
    | lvalue (INC | DEC)+
    ;

// switch: CASE/DEFAULT có thể không có (rỗng)
// nhưng nếu có section thì list_statement KHÔNG được rỗng
// CASE label cũng có thể rỗng: case:
switch_statement
    : SWITCH LPAREN expression RPAREN LBRACE switch_cases* switch_default? switch_cases* RBRACE
    ;

switch_cases
    : CASE expression COLON list_statement?
    ;

switch_default
    : DEFAULT COLON list_statement?
    ;

default_section
    : DEFAULT COLON list_statement
    ;

break_statement
    : BREAK SEMI
    ;

continue_statement
    : CONTINUE SEMI
    ;

return_statement
    : RETURN expression? SEMI
    ;

block_statement
    : LBRACE list_statement? RBRACE
    ;

expression_statement
    : expression SEMI
    ;

// ----------- EXPRESSIONS -----------
// precedence: assignment -> || -> && -> == != -> < <= > >= -> + - -> * / % -> member_access -> unary -> postfix

expression
    : assignment_expr
    ;

/*
 * Nếu assignment của bạn là kiểu "lhs bắt buộc accessed":
 * assignment_expr
 *     : accessed ASSIGN assignment_expr
 *     | logical_or_expr
 *     ;
 *
 * Nếu assignment kiểu thường (phổ biến):
 * assignment_expr
 *     : logical_or_expr (ASSIGN assignment_expr)?
 *     ;
 */



logical_or_expr
    : logical_and_expr (OR logical_and_expr)*
    ;

logical_and_expr
    : equality_expr (AND equality_expr)*
    ;

equality_expr
    : relational_expr ((EQ | NEQ) relational_expr)*
    ;

relational_expr
    : additive_expr ((LT | LE | GT | GE) additive_expr)*
    ;

additive_expr
    : multiplicative_expr ((PLUS | MINUS) multiplicative_expr)*
    ;

multiplicative_expr
    : unary_expr ((MUL | DIV | MOD) unary_expr)*
    ;

/*
 * member_access_expr ở tầng giữa mul và unary:
 * - Cho phép a.b.c
 * - Cho phép foo().a.b (vì call_expr nằm trong unary)
 * - KHÔNG cho a.foo() (method call) vì call_expr base không cho accessed có DOT
 */

/*
 * unary:
 * - Cho phép chuỗi prefix ! + - lặp: !!-+!-+a
 * - Cho phép ++/-- áp lên accessed hoặc (expression): ++(+a)
 * - Cho phép postfix ++/-- trên bất kỳ postfix_expr: "s"++
 */
unary_expr
    : (NOT | PLUS | MINUS)+ unary_expr
    | indec_expr
    | postfix_incdec_any
    | postfix_expr
    | primary
    ;

/*
 * postfix ++/-- trên mọi postfix_expr (để "s"++ hợp lệ)
 */
postfix_incdec_any
    : postfix_expr (INC | DEC)+
    ;

/*
 * inc/dec chain:
 * - a++--++--
 * - ++--++--a++--++--
 * - prefix có thể áp lên accessed hoặc (expression)
 * - postfix chain chỉ chắc chắn trên accessed, nhưng để match test_022, ta cho postfix chain cả trong nhánh 1
 */
indec_expr
  : (INC | DEC)+ incdec_target (INC | DEC)*
  | accessed (INC | DEC)+
  ;
incdec_target
  : accessed
  | paren_expr
  | literal
  ;
paren_expr
    : LPAREN expression RPAREN
    ;

/*
 * postfix_expr:
 * - call_expr (cho phép foo(), (expr)(), ... nếu spec cho)
 * - sau đó mới được .ID chain (để foo().a.b hợp lệ)
 * - TUYỆT ĐỐI KHÔNG cho call sau khi đã có .ID => a.foo() phải lỗi tại '('
 */
postfix_expr
    : member_expr
    ;

member_expr
    : call_expr (DOT ID)*
    ;

/*
 * call_expr chỉ được phép gọi trên call_base,
 * call_base KHÔNG cho accessed dạng a.b.c,
 * nên a.foo() sẽ fail đúng tại '(' (test_028).
 */
call_expr
    : call_base (LPAREN argument_list? RPAREN)?
    ;

call_base
    : ID
    | LPAREN expression RPAREN
    | literal
    ;

/*
 * argument list
 */
argument_list
    : expression (COMMA expression)*
    ;

/*
 * primary:
 * - accessed để dùng như biến/field chain (ID (DOT ID)*)
 * - literal
 * - parenthesized expression
 */
primary
    : literal
    | accessed
    | LPAREN expression RPAREN
    ;


// ----------- LITERALS -----------
// literal có thêm struct_literal và struct_literal có thể rỗng: {}
literal
    : INT_LIT
    | FLOAT_LIT
    | STRING_LIT
    | struct_literal
    ;

struct_literal
    : LBRACE (expression (COMMA expression)*)? RBRACE
    ;


// =====================
//        LEXER
// =====================

// ----- Keywords -----
AUTO        : 'auto';
BREAK       : 'break';
CASE        : 'case';
CONTINUE    : 'continue';
DEFAULT     : 'default';
ELSE        : 'else';
FLOAT       : 'float';
FOR         : 'for';
IF          : 'if';
INT         : 'int';
RETURN      : 'return';
STRING      : 'string';
STRUCT      : 'struct';
SWITCH      : 'switch';
VOID        : 'void';
WHILE       : 'while';

// ----- Operators -----
INC         : '++';
DEC         : '--';
OR          : '||';
AND         : '&&';
EQ          : '==';
NEQ         : '!=';
LE          : '<=';
GE          : '>=';
LT          : '<';
GT          : '>';
ASSIGN      : '=';
PLUS        : '+';
MINUS       : '-';
MUL         : '*';
DIV         : '/';
MOD         : '%';
NOT         : '!';
//DOT         : '.';

// ----- Separators -----

LBRACE      : '{';
RBRACE      : '}';
LPAREN      : '(';
RPAREN      : ')';
SEMI        : ';';
COMMA       : ',';
COLON       : ':';

// ----- Identifiers -----
ID          : [a-zA-Z_] [a-zA-Z0-9_]*;

// ----- Literals -----
FLOAT_LIT
    : DIGITS+ '.' DIGITS* EXP?
    | '.' DIGITS+ EXP?
    | DIGITS+ EXP
    ;

INT_LIT
    : DIGITS+
    ;

// '.' as member-access operator (must come after FLOAT_LIT)
DOT
    : '.'
    ;

STRING_LIT
    : '"' (ESC_SEQ | ~["\\\r\n])* '"'
      { self.text = self.text[1:-1] }
    ;

// ----- Comments & Whitespace -----
BLOCK_COMMENT
    : '/*' .*? '*/' -> skip
    ;

LINE_COMMENT
    : '//' ~[\r\n]* -> skip
    ;

WS
    : [ \t\r\n\f]+ -> skip
    ;

// ----- String Errors -----
ILLEGAL_ESCAPE
    : '"' (ESC_SEQ | ~["\\\r\n])* '\\' ~[btnfr"\\]
      { self.text = self.text[1:] }
    ;

UNCLOSE_STRING
    : '"' (ESC_SEQ | ~["\\\r\n])* ('\r'? '\n' | EOF)
      { self.text = self.text[1:] }
    ;

// ----- Fallback error -----
ERROR_CHAR
    : .
    ;

// ----- Fragments -----
fragment DIGITS  : [0-9]+;
fragment EXP     : [eE] [+-]? DIGITS;
fragment ESC_SEQ : '\\' [btnfr"\\];
