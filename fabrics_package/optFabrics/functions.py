import casadi as ca

def createMapping(phi, name, q, qdot):
    # differential map and jacobian phi : Q -> X
    phi_fun = ca.Function("phi_" + name, [q], [phi])
    J = ca.jacobian(phi, q)
    Jdot = ca.jacobian(ca.mtimes(J, qdot), q)
    J_fun = ca.Function("J_" + name, [q], [J])
    Jdot_fun = ca.Function("Jdot_" + name, [q, qdot], [Jdot])
    return (phi_fun, J_fun, Jdot_fun)

def generateLagrangian(L, q, qdot, name):
    dL_dq = ca.gradient(L, q)
    dL_dqdot = ca.gradient(L, qdot)
    d2L_dq2 = ca.jacobian(dL_dq, q)
    d2L_dqdqdot = ca.jacobian(dL_dq, qdot)
    d2L_dqdot2 = ca.jacobian(dL_dqdot, qdot)

    M = d2L_dqdot2
    F = d2L_dqdqdot
    f_e = -dL_dq
    f = ca.mtimes(ca.transpose(F), qdot) + f_e
    return (M, f)

def generateEnergizer(L, q, qdot, name, n):
    (Me, fe) = generateLagrangian(L, q, qdot, name)
    h = ca.SX.sym("h", n)
    a1 = ca.dot(qdot, ca.mtimes(Me, qdot))
    a2 = ca.dot(qdot, ca.mtimes(Me, h) - fe)
    a = a2/a1
    a_fun = ca.Function('a_' + name, [q, qdot, h], [a])
    return a_fun