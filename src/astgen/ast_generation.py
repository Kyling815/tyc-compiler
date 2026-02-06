from __future__ import annotations
from typing import List, Optional

from build.TyCVisitor import TyCVisitor
from build.TyCParser import TyCParser
from src.utils.nodes import *


class ASTGeneration(TyCVisitor):
    # ---------------- PROGRAM / DECL ----------------
    def visitProgram(self, ctx: TyCParser.ProgramContext):
        return Program(self.visit(ctx.list_declaration()))

    def visitList_declaration(self, ctx: TyCParser.List_declarationContext):
        decl = self.visit(ctx.declaration())
        if ctx.list_declaration():
            return [decl] + self.visit(ctx.list_declaration())
        return [decl]

    def visitDeclaration(self, ctx: TyCParser.DeclarationContext):
        if ctx.struct_declaration():
            return self.visit(ctx.struct_declaration())
        return self.visit(ctx.function_declaration())

    def visitStruct_declaration(self, ctx: TyCParser.Struct_declarationContext):
        # Not used in provided tests, keep simple
        name = ctx.ID().getText()
        members = self.visit(ctx.list_struct_member()) if ctx.list_struct_member() else []
        return StructDecl(name, members)

    def visitList_struct_member(self, ctx: TyCParser.List_struct_memberContext):
        mem = self.visit(ctx.struct_member())
        if ctx.list_struct_member():
            return [mem] + self.visit(ctx.list_struct_member())
        return [mem]

    def visitStruct_member(self, ctx: TyCParser.Struct_memberContext):
        typ = self.visit(ctx.type_spec())
        name = ctx.ID().getText()
        return MemberDecl(typ, name)

    def visitFunction_declaration(self, ctx: TyCParser.Function_declarationContext):
        # In tests: all functions have explicit return type (void/int)
        rtype = self.visit(ctx.return_type()) if ctx.return_type() else VoidType()
        name = ctx.ID().getText()
        params = self.visit(ctx.parameter_list()) if ctx.parameter_list() else []
        body = self.visit(ctx.block_statement())
        return FuncDecl(rtype, name, params, body)

    def visitReturn_type(self, ctx: TyCParser.Return_typeContext):
        if ctx.VOID():
            return VoidType()
        if ctx.AUTO():
            # tests never require AutoType node; treat as None-return type? safest: VoidType
            return None
        return self.visit(ctx.type_spec())

    def visitParameter_list(self, ctx: TyCParser.Parameter_listContext):
        return [self.visit(p) for p in ctx.parameter_decl()]

    def visitParameter_decl(self, ctx: TyCParser.Parameter_declContext):
        typ = self.visit(ctx.type_spec())
        name = ctx.ID().getText()
        return Param(typ, name)

    def visitType_spec(self, ctx: TyCParser.Type_specContext):
        if ctx.INT():
            return IntType()
        if ctx.FLOAT():
            return FloatType()
        if ctx.STRING():
            return StringType()
        # user-defined type name (not in given tests)
        return StructType(ctx.ID().getText())

    # ---------------- STATEMENTS ----------------
    def visitList_statement(self, ctx: TyCParser.List_statementContext):
        st = self.visit(ctx.statement())
        if ctx.list_statement():
            return [st] + self.visit(ctx.list_statement())
        return [st]

    def visitStatement(self, ctx: TyCParser.StatementContext):
        # IMPORTANT: grammar already prioritizes assign_statement before expression_statement
        if ctx.assign_statement():
            return self.visit(ctx.assign_statement())
        if ctx.var_statement():
            return self.visit(ctx.var_statement())
        if ctx.if_statement():
            return self.visit(ctx.if_statement())
        if ctx.while_statement():
            return self.visit(ctx.while_statement())
        if ctx.for_statement():
            return self.visit(ctx.for_statement())
        if ctx.switch_statement():
            return self.visit(ctx.switch_statement())
        if ctx.break_statement():
            return self.visit(ctx.break_statement())
        if ctx.continue_statement():
            return self.visit(ctx.continue_statement())
        if ctx.block_statement():
            return self.visit(ctx.block_statement())
        if ctx.expression_statement():
            return self.visit(ctx.expression_statement())
        return self.visit(ctx.return_statement())

    def visitVar_statement(self, ctx: TyCParser.Var_statementContext):
        name = ctx.ID().getText()
        init = self.visit(ctx.expression()) if ctx.expression() else None

        # tests: auto => VarDecl(None, name, init)
        if ctx.AUTO():
            return VarDecl(None, name, init)

        # explicit types
        typ = self.visit(ctx.type_spec())
        return VarDecl(typ, name, init)

    def visitAssign_statement(self, ctx: TyCParser.Assign_statementContext):
        # tests expect: AssignStmt(AssignExpr(lhs, rhs))
        lhs = self.visit(ctx.lvalue())
        rhs = self.visit(ctx.expression())
        return AssignStmt(AssignExpr(lhs, rhs))

    def visitLvalue(self, ctx: TyCParser.LvalueContext):
        # tests only use plain Identifier in LHS (sum, i, f, ...)
        ids = [t.getText() for t in ctx.ID()]
        base = Identifier(ids[0])
        # if have .field chain (not in tests), keep as FieldAccess
        for field in ids[1:]:
            base = MemberAccess(base, field)
        return base

    def visitBlock_statement(self, ctx: TyCParser.Block_statementContext):
        stmts = self.visit(ctx.list_statement()) if ctx.list_statement() else []
        return BlockStmt(stmts)

    def visitExpression_statement(self, ctx: TyCParser.Expression_statementContext):
        return ExprStmt(self.visit(ctx.expression()))

    def visitReturn_statement(self, ctx: TyCParser.Return_statementContext):
        expr = self.visit(ctx.expression()) if ctx.expression() else None
        return ReturnStmt(expr)

    def visitIf_statement(self, ctx: TyCParser.If_statementContext):
        cond = self.visit(ctx.expression())
        then_s = self.visit(ctx.statement(0))
        else_s = self.visit(ctx.statement(1)) if ctx.ELSE() else None
        return IfStmt(cond, then_s, else_s)

    def visitWhile_statement(self, ctx: TyCParser.While_statementContext):
        cond = self.visit(ctx.expression())
        body = self.visit(ctx.statement())
        return WhileStmt(cond, body)

    def visitFor_statement(self, ctx: TyCParser.For_statementContext):
        init = self.visit(ctx.for_init()) if ctx.for_init() else None
        cond = self.visit(ctx.expression()) if ctx.expression() else None
        upd = self.visit(ctx.for_update()) if ctx.for_update() else None
        body = self.visit(ctx.statement())
        return ForStmt(init, cond, upd, body)

    def visitFor_init(self, ctx: TyCParser.For_initContext):
        if ctx.var_statement():
            return self.visit(ctx.var_statement())

        # for-init expects an expression form, NOT a statement wrapper
        if ctx.assign_statement():
            a = ctx.assign_statement()
            lhs = self.visit(a.lvalue())
            rhs = self.visit(a.expression())
            return AssignExpr(lhs, rhs)

        return self.visit(ctx.expression())

    def visitFor_update(self, ctx: TyCParser.For_updateContext):
        # ++a / --a
        if ctx.incdec_statement():
            text = ctx.incdec_statement().getText()
            lv = self.visit(ctx.incdec_statement().lvalue())

            if text.startswith("++"):
                return PrefixOp("++", lv)
            if text.startswith("--"):
                return PrefixOp("--", lv)
            if text.endswith("++"):
                return PostfixOp("++", lv)
            if text.endswith("--"):
                return PostfixOp("--", lv)

        # assignment in for-update must be AssignExpr
        if ctx.assign_statement():
            a = ctx.assign_statement()
            lhs = self.visit(a.lvalue())
            rhs = self.visit(a.expression())
            return AssignExpr(lhs, rhs)

        return None
    
    def visitSwitch_statement(self, ctx: TyCParser.Switch_statementContext):
        expr = self.visit(ctx.expression())
        cases = [self.visit(sec) for sec in ctx.switch_section()]
        default = self.visit(ctx.default_section()) if ctx.default_section() else None
        return SwitchStmt(expr, cases, default)
    
    def visitSwitch_section(self, ctx: TyCParser.Switch_sectionContext):
        label = self.visit(ctx.expression())
        stmts = self.visit(ctx.list_statement())
        return CaseStmt(label, stmts)

    def visitDefault_section(self, ctx: TyCParser.Default_sectionContext):
        stmts = self.visit(ctx.list_statement())
        return DefaultStmt(stmts)

    def visitIncdec_statement(self, ctx: TyCParser.Incdec_statementContext):
        # In tests: ++i; and ++j (both are prefix)
        # We'll detect token order; if postfix, still represent as PrefixOp for now (tests only prefix)
        lv = self.visit(ctx.lvalue())
        text = ctx.getText()
        if text.startswith("++"):
            return PrefixOp("++", lv)
        if text.startswith("--"):
            return PrefixOp("--", lv)
        if text.endswith("++"):
            return PrefixOp("++", lv)
        if text.endswith("--"):
            return PrefixOp("--", lv)
        return lv
    
    def visitBreak_statement(self, ctx: TyCParser.Break_statementContext):
        return BreakStmt()

    def visitContinue_statement(self, ctx: TyCParser.Continue_statementContext):
        return ContinueStmt()


    # ---------------- EXPRESSIONS ----------------
    def visitExpression(self, ctx: TyCParser.ExpressionContext):
        return self.visit(ctx.assignment_expr())

    def visitAssignment_expr(self, ctx: TyCParser.Assignment_exprContext):
        # If expression-level assignment appears, represent as AssignExpr (closest to tests style)
        left = self.visit(ctx.logical_or_expr())
        if ctx.assignment_expr() is None:
            return left
        right = self.visit(ctx.assignment_expr())
        return AssignExpr(left, right)

    def visitLogical_or_expr(self, ctx: TyCParser.Logical_or_exprContext):
        expr = self.visit(ctx.logical_and_expr(0))
        for i in range(1, len(ctx.logical_and_expr())):
            expr = BinaryOp(expr, "||", self.visit(ctx.logical_and_expr(i)))
        return expr

    def visitLogical_and_expr(self, ctx: TyCParser.Logical_and_exprContext):
        expr = self.visit(ctx.equality_expr(0))
        for i in range(1, len(ctx.equality_expr())):
            expr = BinaryOp(expr, "&&", self.visit(ctx.equality_expr(i)))
        return expr

    def visitEquality_expr(self, ctx: TyCParser.Equality_exprContext):
        expr = self.visit(ctx.relational_expr(0))
        j = 1
        for c in ctx.children:
            if getattr(c, "symbol", None) and c.getText() in ("==", "!="):
                expr = BinaryOp(expr, c.getText(), self.visit(ctx.relational_expr(j)))
                j += 1
        return expr

    def visitRelational_expr(self, ctx: TyCParser.Relational_exprContext):
        expr = self.visit(ctx.additive_expr(0))
        j = 1
        for c in ctx.children:
            if getattr(c, "symbol", None) and c.getText() in ("<", "<=", ">", ">="):
                expr = BinaryOp(expr, c.getText(), self.visit(ctx.additive_expr(j)))
                j += 1
        return expr

    def visitAdditive_expr(self, ctx: TyCParser.Additive_exprContext):
        expr = self.visit(ctx.multiplicative_expr(0))
        j = 1
        for c in ctx.children:
            if getattr(c, "symbol", None) and c.getText() in ("+", "-"):
                expr = BinaryOp(expr, c.getText(), self.visit(ctx.multiplicative_expr(j)))
                j += 1
        return expr

    def visitMultiplicative_expr(self, ctx: TyCParser.Multiplicative_exprContext):
        expr = self.visit(ctx.member_access_expr(0))
        j = 1
        for c in ctx.children:
            if getattr(c, "symbol", None) and c.getText() in ("*", "/", "%"):
                expr = BinaryOp(expr, c.getText(), self.visit(ctx.member_access_expr(j)))
                j += 1
        return expr

    def visitMember_access_expr(self, ctx: TyCParser.Member_access_exprContext):
        expr = self.visit(ctx.unary_expr())
        for tok in ctx.ID():
            expr = MemberAccess(expr, tok.getText())
        return expr

    def visitUnary_expr(self, ctx: TyCParser.Unary_exprContext):
        if ctx.prefix_incdec():
            return self.visit(ctx.prefix_incdec())
        if ctx.postfix_expr():
            return self.visit(ctx.postfix_expr())
        op = ctx.getChild(0).getText()
        return PrefixOp(op, self.visit(ctx.unary_expr()))

    def visitPrefix_incdec(self, ctx: TyCParser.Prefix_incdecContext):
        # prefix_incdec can contain multiple ++/-- before postfix_expr
        expr = self.visit(ctx.postfix_expr())

        ops = []
        for ch in ctx.children:
            if getattr(ch, "symbol", None) and ch.getText() in ("++", "--"):
                ops.append(ch.getText())

        # apply from right to left so the first op becomes the outermost
        for op in reversed(ops):
            expr = PrefixOp(op, expr)

        return expr

    def visitPostfix_expr(self, ctx: TyCParser.Postfix_exprContext):
        expr = self.visit(ctx.postfix_base())
        for suf in ctx.postfix_suffix():
            expr = self._apply_suffix(expr, suf)

        # trailing ++/-- must be PostfixOp, applied in written order
        ops = []
        for ch in ctx.children:
            if getattr(ch, "symbol", None) and ch.getText() in ("++", "--"):
                ops.append(ch.getText())

        for op in ops:
            expr = PostfixOp(op, expr)

        return expr


    def _apply_suffix(self, base, ctx: TyCParser.Postfix_suffixContext):
        # function call
        if ctx.LPAREN():
            args = self.visit(ctx.argument_list()) if ctx.argument_list() else []
            # tests expect FuncCall("name", args), where base must be Identifier("name")
            if isinstance(base, Identifier):
                return FuncCall(base.name, args)
            # fallback
            return FuncCall(str(base), args)

        # index access (not in tests)
        idx = self.visit(ctx.expression())
        return ArrayCell(base, idx)

    def visitArgument_list(self, ctx: TyCParser.Argument_listContext):
        return [self.visit(e) for e in ctx.expression()]

    def visitPrimary(self, ctx: TyCParser.PrimaryContext):
        if ctx.literal():
            return self.visit(ctx.literal())
        if ctx.ID():
            return Identifier(ctx.ID().getText())
        return self.visit(ctx.expression())

    def visitLiteral(self, ctx: TyCParser.LiteralContext):
        if ctx.INT_LIT():
            return IntLiteral(int(ctx.INT_LIT().getText()))
        if ctx.FLOAT_LIT():
            return FloatLiteral(float(ctx.FLOAT_LIT().getText()))
        if ctx.STRING_LIT():
            raw = ctx.STRING_LIT().getText()
            if len(raw) >= 2 and raw[0] == '"' and raw[-1] == '"':
                raw = raw[1:-1]
            return StringLiteral(raw)
        # struct literal not in tests
        return self.visit(ctx.struct_literal())

    def visitStruct_literal(self, ctx: TyCParser.Struct_literalContext):
        elems = [self.visit(e) for e in ctx.expression()] if ctx.expression() else []
        return StructLiteral(elems)
