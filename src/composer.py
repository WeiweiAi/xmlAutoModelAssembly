from libcellml import Component,  Model, Units,  Variable

def compose_bioProcess(new_model_name,selection_dict):
    # input: new_model_name, the name of the new model
    #       selection_dict, the dictionary of the selected models and components {model1:{'components':{comp:compref,..},"annotation":annotation_dict,...}
    #       annotation_dict = {'cellml_path': cellml_path,'mediator': mediator_dict, 'sources': sourceDict , 'sinks':sinkDict}
    #  # output: the new model object
    # species_list = {1:{'varinfo':[],chemical terms:[],anatomy terms:[]},2:{'':[],chemical terms:[],anatomy terms:[]}}
    # Add a new component to the new model
    new_model = Model(new_model_name)
    new_component = Component(new_model_name)
    new_model.addComponent(new_component)
    voi = 't'
    units = Units('second')
    voi = Variable(voi)
    voi.setUnits(units)
    new_component.addVariable(voi)   
    #new_component.setMath(MATH_HEADER)
    # Clone the selected components from the selected models to the new model
    for import_model,model_info in selection_dict.items():
       import_components_dict=model_info['components']
       importComponents_clone(new_model,import_model,import_components_dict)
       
    copyUnits_temp(new_model,import_model)
    print('new_model components',getEntityList(new_model))
    # Add new variables for each unique species to the new component
    # To do: check if the species is selected by the user; now assume all species are selected
    annotator = Annotator()
    annotator.setModel(new_model)
    annotator.clearAllIds()
    annotator.assignAllIds()

    species_list = {}
    flux_list = {}
    def update_unique_process(flux_list,mediator,model):
        unique_flag=True
        if len(flux_list) == 0:
            unique_flag=True
        else:
            for id,flux_dict in flux_list.items():
                v_ss_ID = list(mediator.keys())[0]
                if set(mediator[v_ss_ID]["chemical terms"])& set(flux_dict["chemical terms"]) and set(mediator[v_ss_ID]["anatomy terms"])& set(flux_dict["anatomy terms"]):
                    unique_flag=False                    
                    flux_list[id]["varinfo"].append((model,v_ss_ID))
                    break
        if unique_flag:
            id = len(flux_list)+1
            v_ss_ID = list(mediator.keys())[0]
            flux_list.update({id:{'varinfo':[(model,v_ss_ID)],"chemical terms":mediator[v_ss_ID]["chemical terms"],"anatomy terms":mediator[v_ss_ID]["anatomy terms"]}})

    def update_unique_species(species_list,q_varID,species,participant_location,v_ss_ID,model):
        unique_flag=True
        if len(species_list) == 0:
            unique_flag=True
        else:          
            for id,species_dict in species_list.items():                
                if set(species["anatomy terms"])& set(species_dict["anatomy terms"]) and set(species["chemical terms"])& set(species_dict["chemical terms"]):
                    unique_flag=False
                    species_list[id]["varinfo"].append((model,v_ss_ID,participant_location,species['proportionality'],q_varID))
                    break
        
        if unique_flag:
            id = len(species_list)+1
            species_list.update({id:{'varinfo':[(model,v_ss_ID,participant_location,species['proportionality'],q_varID)],"chemical terms":species["chemical terms"],"anatomy terms":species["anatomy terms"]}})
    # Todo: check if the flux is unique, now assume all fluxes are unique
    for model,model_info in selection_dict.items():
        for bioProc in list(model_info['annotation'].values()):
            v_ss_ID = list(bioProc['mediator'].keys())[0]
            update_unique_process(flux_list,bioProc['mediator'],model)
            for participant_location, participants in bioProc.items():
                # participants = {'q_varID':{'proportionality':1,'physics':[('opb','OPB_00425')] ,'chemical terms':[('chebi','4167')],'anatomy terms': [('go','0005615')]}}
                if participant_location == 'sources':
                    for q_varID, participant in participants.items():
                        update_unique_species(species_list,q_varID,participant,participant_location,v_ss_ID,model)

                if participant_location == 'sinks':
                    for q_varID, participant in participants.items():
                        update_unique_species(species_list,q_varID, participant,participant_location,v_ss_ID,model)
    
    for speciesID, species_info in species_list.items():
        print("species", speciesID, species_info)
        qvar_infos = species_info['varinfo']
        q_var = Variable(f"q_{speciesID}")
        q_var.setInitialValue(1.0)
        new_component.addVariable(q_var)
        ode_var = f'{q_var.name()}'
        new_v_ss_q = f'v_ss_{speciesID}_new'
        new_v_ss = Variable(new_v_ss_q)
        model = qvar_infos[0][0]
        v_ss_ID = qvar_infos[0][1]
        comp_name, fvar_name=getNamebyID(model, v_ss_ID)
        vss_units=model.component(comp_name).variable(fvar_name).units().clone()
        new_v_ss.setUnits(vss_units)
        new_component.addVariable(new_v_ss)
        new_component.appendMath(MATH_HEADER)
        new_component.appendMath(infix_to_mathml(''.join(new_v_ss_q), ode_var,voi="t"))
        new_component.appendMath(MATH_FOOTER)
        eq = []
        # get the units of the quantity variable        
        print('qvar_infos',qvar_infos)
        for qvar_info in qvar_infos:
            model = qvar_info[0]
            v_ss_ID = qvar_info[1]
            participant_location = qvar_info[2]
            coef=qvar_info[3]
            q_varID = qvar_info[4]
            model_info=selection_dict[model]
            qimport_components_dict=model_info['components']
            print('qimport_components_dict',qimport_components_dict)
            qcomp_name, qvar_name=getNamebyID(model, q_varID)
            qvar_units=model.component(qcomp_name).variable(qvar_name).units().clone()
            q_var.setUnits(qvar_units)
            for component in list(qimport_components_dict.keys()):
                if qcomp_name == qimport_components_dict[component]:
                    Variable.addEquivalence(new_component.variable(q_var.name()), new_model.component(component).variable(qvar_name))
                    break

            for fluxID, mediator_info in flux_list.items():
                print('flux',fluxID, mediator_info)
                flux_infos = mediator_info['varinfo']
                for flux_info in flux_infos:
                    model_f = flux_info[0]
                    v_ss_ID_f = flux_info[1]
                    if model == model_f and v_ss_ID == v_ss_ID_f:
                        comp_name, fvar_name=getNamebyID(model_f, v_ss_ID)
                        model_info=selection_dict[model_f]
                        import_components_dict=model_info['components']
                        for component in list(import_components_dict.keys()):
                           if comp_name == import_components_dict[component]:                              
                               var_list=getEntityList(new_model,new_model.name())
                               # get the end of the component name to avoid duplication
                               compid=component.split('_')[-1]
                               new_v_ss_name = f'{fvar_name}_{compid}'
                               if new_v_ss_name not in var_list:
                                      new_v_ss = Variable(new_v_ss_name)
                                      vss_units=model_f.component(comp_name).variable(fvar_name).units().clone()
                                      new_v_ss.setUnits(vss_units)
                                      new_component.addVariable(new_v_ss)                                      
                                      Variable.addEquivalence(new_component.variable(new_v_ss_name), new_model.component(component).variable(fvar_name))
                               else:
                                      Variable.addEquivalence(new_component.variable(new_v_ss_name), new_model.component(component).variable(fvar_name))                                                                    
                        if participant_location == 'sources':
                            if coef == 1:
                                eq.append(f'-{fvar_name}_{compid}')
                            else:
                                eq.append(f'-{coef}*{fvar_name}_{compid}')
                        elif participant_location == 'sinks':
                            if coef == 1:
                                if len(eq) == 0:
                                    eq.append(f'{fvar_name}_{compid}')
                                else:
                                    eq.append(f'+{fvar_name}_{compid}')
                            else:
                                if len(eq) == 0:
                                    eq.append(f'{coef}*{fvar_name}_{compid}')
                                else:
                                    eq.append(f'+{coef}*{fvar_name}_{compid}')
        new_component.appendMath(MATH_HEADER)
        new_component.appendMath(infix_to_mathml(''.join(eq), new_v_ss_q))
        new_component.appendMath(MATH_FOOTER)
    new_model.fixVariableInterfaces()            
    return new_model