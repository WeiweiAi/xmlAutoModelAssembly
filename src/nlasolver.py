from sundials import cvode, cvode_ls, sundials_context, nvector_serial, sunmatrix_dense, sunlinsol_dense, sundials_matrix, sundials_nvector, sundials_types, kinsol, kinsol_ls


# int func(N_Vector y, N_Vector f, void *userData)
# {
#     UserNlaData *realUserData = (UserNlaData *) userData;
#
#     realUserData->objectiveFunction(N_VGetArrayPointer_Serial(y), N_VGetArrayPointer_Serial(f), realUserData->data);
#
#     return 0;
# }


def func(_y, _f, _user_data):
    y_ = nvector_serial.N_VConvertArray_Serial(_y)
    f_ = nvector_serial.N_VConvertArray_Serial(_f)

    _user_data["obj_func"](y_, f_, _user_data["data"])

    nvector_serial.N_VUpdate_Serial(_y, y_)
    nvector_serial.N_VUpdate_Serial(_f, f_)

    return 0


def nla_solve(objective_function_0, u, n, data):
    # SUNContext context;

    context_ptr = sundials_context.SUNContext_Define()
    sundials_context.SUNContext_Create(None, context_ptr)

    context = sundials_context.SUNContext_Context(context_ptr)

    # Create our KINSOL solver.

    solver = kinsol.KINCreate(context)

    # Initialise our KINSOL solver.

    y = nvector_serial.N_VMake_Serial(n, u, context)

    kinsol.KINInit(solver, func, y)

    # Set our user data.

    user_data = {"obj_func": objective_function_0, "data": data}

    kinsol.KINSetUserData(solver, user_data)

    # Set our maximum number of steps.

    kinsol.KINSetMaxNewtonStep(solver, 99999)

    # Set our linear solver.

    matrix = sunmatrix_dense.SUNDenseMatrix(n, n, context)
    linearSolver = sunlinsol_dense.SUNLinSol_Dense(y, matrix, context)

    kinsol_ls.KINSetLinearSolver(solver, linearSolver, matrix)

    # Solve our linear system.

    scale = nvector_serial.N_VNew_Serial(n, context)

    sundials_nvector.N_VConst(1.0, scale)

    kinsol.KINSol(solver, y, kinsol.KIN_LINESEARCH, scale, scale)

    # // Clean up after ourselves.

    # N_VDestroy(scale);
    # SUNLinSolFree(linearSolver);
    # SUNMatDestroy(matrix);
    # N_VDestroy_Serial(y);
    # KINFree(&solver);
    # SUNContext_Free(&context);

    return nvector_serial.N_VConvertArray_Serial(y)
