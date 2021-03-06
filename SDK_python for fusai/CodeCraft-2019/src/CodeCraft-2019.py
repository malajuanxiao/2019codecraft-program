# -*- coding: utf-8 -*-
import logging
import sys

'''
logging.basicConfig(level=logging.DEBUG,
                    filename='../logs/CodeCraft-2019.log',
                    format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')
'''





'''
注:相比初赛,复赛的优化方向有两个，1.路径规划，2.批量启动调整,3.队列优先级调整,4.地图信息的更新方式
'''
'''
读取文件
'''
def read_data(filename):
    new_list = []
    for line in open(filename,'r'): #设置文件对象并读取每一行文件
        #= line[:-1].split(":")[0]
        if line[0] != '#' :
            line_list = line.rstrip()[1:-1].split(',')
            for idx,item in enumerate(line_list):
                line_list[idx] = int(item)
            new_list.append(line_list)
    return new_list

'''
读取汽车队列
'''
def read_car_data(carfilename):
    pp_list = []
    preset_list = []
    pricar_list = []
    nomcar_list = []
    car_sum = 0
    for line in open(carfilename,'r'): #设置文件对象并读取每一行文件
        if line[0] != '#' :
            car_sum += 1
            line_list = line.rstrip()[1:-1].split(',')
            for idx,item in enumerate(line_list):
                line_list[idx] = int(item)
            if int(line_list[-1]) == 1 and int(line_list[-2]) == 1:
                pp_list.append(line_list)
            elif int(line_list[-1]) == 1:
                preset_list.append(line_list)
            elif int(line_list[-2]) == 1:
                 pricar_list.append(line_list)
            else:
                nomcar_list.append(line_list)
    return pp_list,preset_list,pricar_list,nomcar_list,car_sum


'''
关于路径更新公式
原先更新是这个样子
如 len(i) + min < len(j) 则 len(j) = len(i) + min
对于len(i)先后添加的影响因素，这些都是试出来的，有些因素乘以或除以一个变量就会产生比较大的影响，
1.道路车辆数对长度的转换（这里是把车辆的长度当作是1）
2.当前拥塞程度（这个公式最难解释，没有除以车道数，反正改成0.5的定值加上去就是最有效果）
3.长度更新转时间更新（时间最短更新跟符合常理）
4.地图铺满程度因子（作为权重加强长度装换的影响，目标是尽可能的让车辆铺满）
现在len(i)大概是这个样子
len(i)=> （长度更新转时间更新 + 地图铺满程度*道路车辆数对长度的转换） + 当前拥塞程度 

findBestPath参数:车号，车辆信息字典，路口情况字典，道路情况字典，当前最大的道平均车辆数

'''
def findBestPath(car,carStatus_dict,cross_dict,index_dict,max_sum):
    vexnum = len(cross_dict)
    #print(carStatus_dict[car]) 
    from_id = carStatus_dict[car][4]
    to_id = carStatus_dict[car][5]
    speed = carStatus_dict[car][2]
    #start_time = carStatus_dict[car][3]
    have =[False] * vexnum
    distance = [1000000] * vexnum
    #print(index_dict)
    from_index_id = list(index_dict.keys())[list(index_dict.values()).index(from_id )]
    to_index_id = list(index_dict.keys())[list(index_dict.values()).index(to_id)]
    distance[from_index_id] = 0
    destination = [0] * vexnum
    path = []

    #print(cross_dict[1])

    for d in range(vexnum):
        min = 1000000
        update_id = 0
        for i in range(vexnum):
            if have[i] != True and distance[i] < min:
                min = distance[i]
                update_id = i
        have[update_id] = True
        #update_id +=1
         
        for item in cross_dict[index_dict[update_id]]:
            next_update_id = list(index_dict.keys())[list(index_dict.values()).index(item[0])]
            #road_speed = road_dict[item[1]][4]
            #print(road_speed)
            now_speed = speed if speed < item[5] else item[5]
            K=1
            if item[6]> 1:
                K = (2 - (max_sum - item[6])/ max_sum) * 2
            #(item[3]/speed) 2* (item[3] * item[5] )/(item[2] *speed) 
            '''
            item为节点（路口）信息
            原始长度转换为：长度+ 道平均车辆数
            now_speed:表示当前方道路没有堵塞，车辆正常的行驶速度，取车速与限速最小值
            K:地图铺满程度因子  当前道平均车辆数（走过该条道路的历史车辆数/该条道路的道数）大于一定值（这里取50）时，进行判断，得出的K要>=1
            这种加重长度影响是为了动态的以当前最拥挤的道路为基准 让车辆选择其他道路使得尽量跟最拥挤的道路一样拥挤 
            这个是最后一次能提升批量启动车辆数的因素
            拥塞程度: 0.5* (走过该条道路的历史车辆数/道路长度）  这个属玄学
            
            item[2]:两节点之间的道路长度
            item[3]:两节点之间的道路的历史车辆数
            item[4]:两节点之间的道路道数
            item[5]:两节点之间的道路限速
            item[6]:两节点之间的当前道平均车辆数
            ...
            '''
            if item[2]/now_speed +  K*(item[3]/item[4]) + 0.5*(item[3]/item[2]) + min < distance[next_update_id]:#这里涉及下一路径的判断，关于剩余道路数，下一节点的
                distance[next_update_id] = item[2]/now_speed +  K*(item[3]/item[4]) + 0.5*(item[3]/item[2]) + min
                destination[next_update_id] = update_id
            '''
            
            if item[2] * item[4] /now_speed +  K*(item[3]/item[4]) + 0.5*(item[3]/(item[2] * item[4])) + min < distance[next_update_id]:#这里涉及下一路径的判断，关于剩余道路数，下一节点的
                distance[next_update_id] = item[2] * item[4] /now_speed +  K*(item[3]/item[4]) + 0.5*(item[3]/(item[2] * item[4])) + min
                destination[next_update_id] = update_id
            '''
    
    path = [to_index_id]
    while True:
        if destination[to_index_id] != from_index_id:
            to_index_id = destination[to_index_id]
            path = [to_index_id] + path 
        else:
            break
    path = [from_index_id] + path
    #print(path)
    #print(distance)    
    #print(destination) 
    return path
'''
有修改
每一趟车选完路径后，就会更新一次全局信息，初赛是是直接清零的，后来发现应该乘以缩放比例，保留还未走完的一些车辆的信息,这样感觉比较合理
关于地图信息
除了这里的重置之外,后面的车辆规划路线操作上加了超前补充和超前回撤,
超前补充:每个时间间隔将 后发影响的预置车辆考虑进去,因为有可能在这些后发预置路线出现死锁问题
超前回撤:同时结束清空这些影响,以免造成后面的信息混乱
最后和初赛一样,每个地图信息的的更新细节与每辆车的规划操作有关
'''   
def reset(cross_dict,max_sum,n_ratio):
    max_sum *= n_ratio
    for cross_key in cross_dict:
        for i in range(len(cross_dict[cross_key])):
            cross_dict[cross_key][i][3]*=(n_ratio)
            cross_dict[cross_key][i][6]*=(n_ratio)







def main():
    if len(sys.argv) != 6:
        logging.info('please input args: car_path, road_path, cross_path, answerPath')
        exit(1)

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    preset_answer_path = sys.argv[4]
    answer_path = sys.argv[5]

    '''
    logging.info("car_path is %s" % (car_path))
    logging.info("road_path is %s" % (road_path))
    logging.info("cross_path is %s" % (cross_path))
	logging.info("preset_answer_path is %s" % (preset_answer_path))
    logging.info("answer_path is %s" % (answer_path))
    '''    
    
    
    
    
    #(id,length,speed,channel,from,to,isDuplex)
    road_list = read_data(road_path)
    #(id,roadId,roadId,roadId,roadId)
    cross_list = read_data(cross_path)
    
    
    '''
    preset_dict 
    预置车辆的状态
    car_id: [actualTime,road_id,road_id,road_id....]# 道路数，当前车辆数，历史车辆数，后面接道数空闲情况
    '''
    #处理预置列表
    preset_answer_list = read_data(preset_answer_path)
    preset_answer_list.sort(key = lambda preset_answer_list:(preset_answer_list[1]))
    preset_dict = {}
    for preset in preset_answer_list:
        preset_info = preset_dict.setdefault(preset[0], []) 
        for i in range(len(preset)-1):
            preset_info.append(preset[i+1])
            
    '''
    汽车队列分为4种  预置且优先pp_list，预置preset_list，优先pricar_list，普通nomcar_list 
    事实上pp_list和preset_list处理方式是一样的但还是分开处理了
    '''
    #(id,from,to,speed,planTime, priority, preset)
    pp_list,preset_list,pricar_list,nomcar_list,carsum = read_car_data(car_path)
    pp_list.sort(key = lambda pp_list:(pp_list[4],pp_list[3]) )
    preset_list.sort(key = lambda preset_list:(preset_list[4],preset_list[3]) )
    pricar_list.sort(key = lambda pricar_list:(pricar_list[4],pricar_list[3]) )
    nomcar_list.sort(key = lambda nomcar_list:(nomcar_list[4],nomcar_list[3]) )
    #print(preset_answer_list[::1000],len(pp_list),len(preset_list),len(pricar_list),len(nomcar_list),carsum)
    

    
    #重整一些地图信息
    '''
    路表信息
    cross_dict
    cross_id:[[cross_id,road_id,length,his_carsum,chnnalsum,limit_speed,ave_carsum]..]
    每一辆车选完路径后，就会更新一次信息，为后续的启动车辆作参考
    
    映射信息
    index_dict
    index_id:cross_id
    
    记录每条路的当前信息
    road_dict 
    road_id : [chnnalsum,carsum,hissum,speed,cur_speed,speed_list,res_channel....]#道路数，当前车辆数，历史车辆数，限速，当前上路车辆中的最小速度，目前在路上的速度列表，后面接道数空闲情况
    这个想结合定时器弄的，这个后来没用,不过先保留下来
    road_dict 
    road_id : [from,to]
    
    要分配路径的车辆状态(只有非预置的车辆需要分配路径)
    carStatus_dict
    car_id:[from,to,speed,startTime,cur_fromid,cur_toid,short_path,cur_speed]
    '''
    
    cross_dict = {}
    road_dict = {}
    index_dict = {}
    #地图信息，之后会考虑规模问题
    total_len = 0 
    total_channal = 0
    total_cross = len(cross_list)
    total_road = len(road_list)
    for i,road in enumerate(road_list):
        cross_info = cross_dict.setdefault(road[4], []) 
        cross_info.append([road[5],road[0],road[1],0,road[3],road[2],0]) 
        road_info = road_dict.setdefault(road[0], [])
        road_info.extend([road[4],road[5]])
        total_len += road[1]*road[3]
        total_channal += road[3]
        if road[6] == 1:
            cross_info = cross_dict.setdefault(road[5], []) 
            cross_info.append([road[4],road[0],road[1],0,road[3],road[2],0])
            total_len += road[1]*road[3]
            total_channal += road[3]
               
    for i,cross in enumerate(cross_list):
        index_dict[i] = cross[0]
    
    
    
    carStatus_dict = {}
    for car in pp_list:
        car_info = carStatus_dict.setdefault(car[0], []) 
        car_info.extend([car[1],car[2],car[3],car[4],car[1],car[2],[],car[3]]) 
    for car in preset_list:
        car_info = carStatus_dict.setdefault(car[0], []) 
        car_info.extend([car[1],car[2],car[3],car[4],car[1],car[2],[],car[3]]) 
        
    for car in pricar_list:
        car_info = carStatus_dict.setdefault(car[0], []) 
        car_info.extend([car[1],car[2],car[3],car[4],car[1],car[2],[],car[3]]) 
    for car in nomcar_list:
        car_info = carStatus_dict.setdefault(car[0], []) 
        car_info.extend([car[1],car[2],car[3],car[4],car[1],car[2],[],car[3]]) 
    
    
    
    
    
    '''
    关于批量启动,初赛代码比较详细,不在累赘
    综合初赛 和复赛的各种地图后我们的间隔扩大比例为
    ratio = (total_len**(1/3)/25 + total_channal/25 + total_cross/25) * 1.2
    
    关于优先级调整
    优先考虑预置车辆先行,因为他们的出发时间是固定的,然后是优先车辆,考虑到他们对系统评优的影响,
    计划出发顺序(以下):
        预置且优先pp_list，
        预置preset_list，
        优先pricar_list，
        普通nomcar_list 
    在进行记车辆录路线操作之前,先记录每个时间间隔的预置车辆,有助于及时调整非预置车辆的行驶情况
    复赛当天,改了要求,预置车辆有一定比例(10%)是改变行驶路线的,于是在pp_list和preset_list做了相应的比例分割调整
    同样,为节省时间，优先级调整也可边处理边写文件
    '''
    #时间迁移，延迟时间，启动汽车规模，
    cur_time = 0
    lay_time = 35
    l_ratio = (total_len**(1/3))/25 + total_channal/25 + total_cross/25
    limit_car = int(lay_time * l_ratio *1.25)
    #limit_car = 2000
    #记载每个队列的输出位置
    pp_pos = 0
    pre_pos = 0
    pri_pos = 0
    nom_pos = 0
    #需要迭代的次数
    iter_t = int(carsum/limit_car) + 1
    max_sum = 0 #记载地图中最拥挤的道路
    n_ratio = 1/3 #重置时的缩放比例
    u_ratio = 1
    lay_sum = 50
    
    
    #先记录每个时间间隔的预置车辆
    pd_list = []
    app_list = []
    apre_list = []
    time_list = []
    for dx in range(iter_t + 21):
        next_time = cur_time + lay_time
        pnsum = 0
        presum = 0
        rest = 0
        
        #优先且预置先行
        for i in range(pp_pos, len(pp_list)):
            pn_info = preset_dict[pp_list[pp_pos][0]]
            if pn_info[0] <= next_time:# and pnsum < limit_car:
                pp_pos += 1
                pnsum += 1
            else:
                 break
        #预置
        for i in range(pre_pos, len(preset_list)):
            pre_info = preset_dict[preset_list[pre_pos][0]]
            if pre_info[0] <= next_time:# and (pnsum + presum) < limit_car:
                pre_pos += 1
                presum += 1
            else:
                 break
             
        cur_time = int(next_time + (pnsum + presum)/(lay_sum))
        app_list.append(pnsum)
        apre_list.append(presum)
        pd_list.append(pnsum + presum)
        time_list.append(cur_time)
        
        
        
    
        
                
    
        
    
    #记载每个队列的输出位置
    pp_pos = 0
    pre_pos = 0
    pri_pos = 0
    nom_pos = 0
    cur_time = 0
    c_ratio = 0.9#复赛应变加的 有0.1比例的车辆可应变发挥,0.9将保持不变
    file = open(answer_path,'w') 
    file.write("#(carId,StartTime,RoadId...)" +'\n')
    
    
               
               
    for dx in range(iter_t + 20):
        rlimit_car = limit_car
        next_time = time_list[dx]
        pnsum = 0
        presum = 0
        prisum = 0
        nomsum = 0
        rest = 0
        
        if app_list[dx] > 0:
            ss_app = int(app_list[dx] * c_ratio) + 1
        else:
            ss_app = 0
            
        if apre_list[dx] > 0:
            ss_apre = int(apre_list[dx] * c_ratio) + 1
        else:
            ss_apre = 0
        
        
        #优先且预置先行,路线保留比例
        for i in range(pp_pos, pp_pos + ss_app):
            pn_info = preset_dict[pp_list[pp_pos][0]]
            #路径规划操作
            for ri in  range(1,len(pn_info)):
                now_id = road_dict[pn_info[ri]][0]
                next_id = road_dict[pn_info[ri]][1]
                for cross_h in cross_dict[now_id]:
                    if cross_h[0] == next_id:
                        cross_h[3] += 1
                        cross_h[6] += (1/cross_h[4])
                        max_sum = max_sum if max_sum > cross_h[6] else cross_h[6]
            pp_pos += 1
            pnsum += 1
        #预置,路线保留比例
        for i in range(pre_pos, pre_pos + ss_apre):
            pre_info = preset_dict[preset_list[pre_pos][0]]
            #路径规划操作
            for ri in  range(1,len(pre_info)):
                now_id = road_dict[pre_info[ri]][0]
                next_id = road_dict[pre_info[ri]][1]
                for cross_h in cross_dict[now_id]:
                    if cross_h[0] == next_id:
                        cross_h[3] += 1
                        cross_h[6] += (1/cross_h[4])
                        max_sum = max_sum if max_sum > cross_h[6] else cross_h[6]
            pre_pos += 1
            presum += 1
            
        
        
        
        
        
        
        
        
        #优先且预置先行,路线可变比例
        for i in range(pp_pos, pp_pos + (app_list[dx] - ss_app)):
            car_no =  pp_list[pp_pos][0] 
            car_path = []
            path = findBestPath(car_no,carStatus_dict,cross_dict,index_dict,max_sum)
            for i in range(1,len(path)):
                now_id = index_dict[path[i-1]]
                next_id = index_dict[path[i]]
                for cross_h in cross_dict[now_id]:
                    if cross_h[0] ==  next_id:
                        road_id = cross_h[1]
                        #地图信息的的更新细节
                        cross_h[3] += 1
                        cross_h[6] += (1/cross_h[4])
                        max_sum = max_sum if max_sum > cross_h[6] else cross_h[6]
                car_path.append(road_id)
                
            res_str = "(" + str(car_no) + "," + str(pp_list[pp_pos][4]) + "," + str(car_path)[1:-1] + ")"
            file.write(res_str +'\n')
            
            
            pp_pos += 1
            pnsum += 1
        #预置,路线可变比例
        for i in range(pre_pos, pre_pos + (apre_list[dx] - ss_apre)):
            
            car_no =  preset_list[pp_pos][0] 
            car_path = []
            path = findBestPath(car_no,carStatus_dict,cross_dict,index_dict,max_sum)
            for i in range(1,len(path)):
                now_id = index_dict[path[i-1]]
                next_id = index_dict[path[i]]
                for cross_h in cross_dict[now_id]:
                    if cross_h[0] ==  next_id:
                        #print(cross_h)
                        road_id = cross_h[1]
                        cross_h[3] += 1
                        cross_h[6] += (1/cross_h[4])
                        max_sum = max_sum if max_sum > cross_h[6] else cross_h[6]
                car_path.append(road_id)
                
            res_str = "(" + str(car_no) + "," + str(preset_list[pp_pos][4]) + "," + str(car_path)[1:-1] + ")"
            file.write(res_str +'\n')
            
            pre_pos += 1
            presum += 1
        
        
        
        '''
        超前补充
        '''
        #优先且预置先行
        for i in range(pp_pos, pp_pos + app_list[dx+1]):
            pn_info = preset_dict[pp_list[i][0]]
            #路径规划操作
            for ri in  range(1,len(pn_info)):
                now_id = road_dict[pn_info[ri]][0]
                next_id = road_dict[pn_info[ri]][1]
                for cross_h in cross_dict[now_id]:
                    if cross_h[0] == next_id:
                        cross_h[3] += u_ratio
                        cross_h[6] += (1/cross_h[4])*u_ratio
                        max_sum = max_sum if max_sum > cross_h[6] else cross_h[6]
        
        #预置
        for i in range(pre_pos, pre_pos +apre_list[dx+1]):
            pre_info = preset_dict[preset_list[i][0]]
            #路径规划操作
            for ri in  range(1,len(pre_info)):
                now_id = road_dict[pre_info[ri]][0]
                next_id = road_dict[pre_info[ri]][1]
                for cross_h in cross_dict[now_id]:
                    if cross_h[0] == next_id:
                        cross_h[3] += u_ratio
                        cross_h[6] += (1/cross_h[4])*u_ratio
                        max_sum = max_sum if max_sum > cross_h[6] else cross_h[6]
        
        #if (pnsum + presum) > 1000 and pd_list[dx+1] > 500:
        #预置车辆行驶完是,这里对当前间隔的剩余行驶车辆进行判断,预置车辆行驶的路线毕竟是死的,塞太多就会堵
        if (pd_list[dx]) < limit_car:
            rlimit_car = int(limit_car - pd_list[dx+1]*1.5)
        '''
        if pd_list[dx+1] > 500:
            #cur_time = next_time
            cur_time = int(next_time + (pd_list[dx])/(lay_sum))
            reset(cross_dict,max_sum,n_ratio)
            continue
        '''
        '''
        if (pd_list[dx]) > 1000 and pd_list[dx+1] <= 500: 
            rlimit_car = int(limit_car + pd_list[dx] - (pd_list[dx] + pd_list[dx+1]) * 1.1)
        '''
        '''
        if(pd_list[dx] == 0):
            rlimit_car = int(limit_car * 1.05)
        '''
        
        #优先车辆
        for i in range(pri_pos, len(pricar_list)):
            if pricar_list[pri_pos][4] <= next_time and (pd_list[dx] + prisum) < rlimit_car:
                #路径规划操作
                car_no = pricar_list[pri_pos][0] 
                car_path = []
                path = findBestPath(car_no,carStatus_dict,cross_dict,index_dict,max_sum)
                for i in range(1,len(path)):
                    now_id = index_dict[path[i-1]]
                    next_id = index_dict[path[i]]
                    for cross_h in cross_dict[now_id]:
                        if cross_h[0] ==  next_id:
                            #print(cross_h)
                            road_id = cross_h[1]
                            cross_h[3] += 1
                            cross_h[6] += (1/cross_h[4])
                            max_sum = max_sum if max_sum > cross_h[6] else cross_h[6]
                    car_path.append(road_id)
                    
                
                car_go = cur_time if cur_time > pricar_list[pri_pos][4] else pricar_list[pri_pos][4]
                res_str = "(" + str(car_no) + "," + str(car_go) + "," + str(car_path)[1:-1] + ")"
                #print(res_str)
                file.write(res_str +'\n')
                pri_pos += 1
                prisum += 1
            else:
                 break
        
        
        rest = rlimit_car - (pd_list[dx] + prisum)  if (pd_list[dx] + prisum) < rlimit_car else 0
        rest = rest if len(nomcar_list)- nom_pos > rest else len(nomcar_list)- nom_pos
        
        #剩余普通车辆
        for i in range(nom_pos, nom_pos + rest):
            #路径规划操作
            car_no = nomcar_list[nom_pos][0]
            car_path = []
            path = findBestPath(car_no,carStatus_dict,cross_dict,index_dict,max_sum)
            for i in range(1,len(path)):
                now_id = index_dict[path[i-1]]
                next_id = index_dict[path[i]]
                for cross_h in cross_dict[now_id]:
                    if cross_h[0] ==  next_id:
                        #print(cross_h)
                        road_id = cross_h[1]
                        cross_h[3] += 1
                        cross_h[6] += (1/cross_h[4])
                        max_sum = max_sum if max_sum > cross_h[6] else cross_h[6]
                car_path.append(road_id)
           
            car_go = cur_time if cur_time > nomcar_list[nom_pos][4] else nomcar_list[nom_pos][4]
            res_str = "(" + str(car_no) + "," + str(car_go) + "," + str(car_path)[1:-1] + ")"
            #print(res_str)
            file.write(res_str +'\n')
            
            nom_pos += 1
            nomsum += 1
        
        '''
        超前回撤
        '''
        #优先且预置先行
        for i in range(pp_pos, pp_pos + app_list[dx+1]):
            pn_info = preset_dict[pp_list[i][0]]
            #路径规划操作
            for ri in  range(1,len(pn_info)):
                now_id = road_dict[pn_info[ri]][0]
                next_id = road_dict[pn_info[ri]][1]
                for cross_h in cross_dict[now_id]:
                    if cross_h[0] == next_id:
                        cross_h[3] -= u_ratio
                        cross_h[6] -= (1/cross_h[4])*u_ratio
                        max_sum = max_sum if max_sum > cross_h[6] else cross_h[6]
            
        #预置
        for i in range(pre_pos, pre_pos +apre_list[dx+1]):
            pre_info = preset_dict[preset_list[i][0]]
            #路径规划操作
            for ri in  range(1,len(pre_info)):
                now_id = road_dict[pre_info[ri]][0]
                next_id = road_dict[pre_info[ri]][1]
                for cross_h in cross_dict[now_id]:
                    if cross_h[0] == next_id:
                        cross_h[3] -= u_ratio
                        cross_h[6] -= (1/cross_h[4])*u_ratio
                        max_sum = max_sum if max_sum > cross_h[6] else cross_h[6]
        
        #cur_time = next_time
        cur_time = time_list[dx]
        
        #print("第",dx,"次:","时间:", cur_time," 数目:",pd_list[dx],prisum,rest, "预置指向时间:", preset_dict[preset_list[pre_pos-1][0]][0])
        reset(cross_dict,max_sum,n_ratio)
    file.close()   
    
    #print("保存文件成功")



if __name__ == "__main__":
    main()