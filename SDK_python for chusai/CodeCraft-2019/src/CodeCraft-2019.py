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

注:优化的方向有两个，一个是路径规划，一个是批量启动调整

'''




'''
读取文件
'''
def read_data(filename):
    new_list = []
    for line in open(filename,'r'): 
        #= line[:-1].split(":")[0]
        if line[0] != '#' :
            line_list = line.rstrip()[1:-1].split(',')
            for idx,item in enumerate(line_list):
                line_list[idx] = int(item)
            if 'car' in filename:
                line_list.append(0);
            new_list.append(line_list)
    return new_list



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


#寻找最优路径
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
            next_update_id = list(index_dict.keys())[list(index_dict.values()).index(item[0])]
            #road_speed = road_dict[item[1]][4]
            #print(road_speed)
            now_speed = speed if speed < item[5] else item[5]
            K=1
            if item[6]> 50:
                K = (2 - (max_sum - item[6])/ max_sum) * 2
            #(item[3]/speed) 2* (item[3] * item[5] )/(item[2] *speed)   
            if item[2]/now_speed +  K*(item[3]/item[4]) + 0.5*(item[3]/item[2]) + min < distance[next_update_id]:#这里涉及下一路径的判断，关于剩余道路数，下一节点的
                distance[next_update_id] = item[2]/now_speed +  K*(item[3]/item[4]) + 0.5*(item[3]/item[2]) + min
                destination[next_update_id] = update_id
           
    
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

地图状况重置函数 每一批量的汽车走完 清空所有路表状态，为下一个批量的运行做准备

'''    
def reset(cross_dict):
    for cross_key in cross_dict:
        for i in range(len(cross_dict[cross_key])):
            cross_dict[cross_key][i][3]=0
            cross_dict[cross_key][i][6]=0




def main():
    if len(sys.argv) != 5:
        logging.info('please input args: car_path, road_path, cross_path, answerPath')
        exit(1)

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    answer_path = sys.argv[4]

    logging.info("car_path is %s" % (car_path))
    logging.info("road_path is %s" % (road_path))
    logging.info("cross_path is %s" % (cross_path))
    logging.info("answer_path is %s" % (answer_path))
    
    # to read input file
    
    #(id,length,speed,channel,from,to,isDuplex)
    road_list = read_data(road_path)
    #(id,roadId,roadId,roadId,roadId)
    cross_list = read_data(cross_path)
    #(id,from,to,speed,planTime，havestop)
    car_list = read_data(car_path)
    car_list.sort(key = lambda car_list:(car_list[4],car_list[3]) )
    
    
    # process
    
    '''
    路表信息
    cross_id:[[cross_id,road_id,length,his_carsum,chnnalsum,limit_speed,ave_carsum]..]
    每一辆车选完路径后，就会更新一次信息，为后续的启动车辆作参考
    
    road_dict 这个后来没用  不过先保留下来
    记录每条路的当前状态状态
    
    road_id : [chnnalsum,carsum,hissum,speed,cur_speed,speed_list,res_channel....]# 道路数，当前车辆数，历史车辆数，后面接道数空闲情况
    路标映射字典
    index_dict  
    '''


    cross_dict = {}
    road_dict = {}
    index_dict = {}
    
    total_len = 0 
    total_channal = 0
    #total_cross = len(cross_list)
    #total_road = len(road_list)
    for i,road in enumerate(road_list):
        cross_info = cross_dict.setdefault(road[4], []) 
        cross_info.append([road[5],road[0],road[1],0,road[3],road[2],0]) 
        road_info = road_dict.setdefault(road[0], [])
        road_info.extend([road[3],0,0,road[2],road[2],[],road[3]])
        total_len += road[1]*road[3]
        total_channal += road[3]
        if road[6] == 1:
            cross_info = cross_dict.setdefault(road[5], []) 
            cross_info.append([road[4],road[0],road[1],0,road[3],road[2],0])
            total_len += road[1]*road[3]
            total_channal += road[3]
            
            
    for i,cross in enumerate(cross_list):
        index_dict[i] = cross[0]
    #print(cross_dict)
    #print(road_dict)



    '''
    carStatus_dict
    记录每辆车的车辆状态，用得比较少
    car_id:[from,to,speed,startTime,cur_fromid,cur_toid,have_cross,cur_speed,road_id,channal_id,short_path,next_cross,next_updatetime]
    '''
    carStatus_dict = {}
    

    for car in car_list:
        car_info = carStatus_dict.setdefault(car[0], []) 
        car_info.extend([car[1],car[2],car[3],car[4],car[1],car[2],[],car[3]]) 
    
    #print(carStatus_dict)
    
    
    
    
    '''
    关于批量启动
    目前两个方案
    A.约一批车辆跑完的间隔的大批量调动
    B.定间隔小批量调动，
    
    地图1 2上
    A方案极限最短740
    B方案极限最短695
    
    感觉第B方案好一点，但没有完全舍弃A方案（代码文件还保留），比赛毕竟存在很多不确定因素，万一A方案效果更好
    保留了A方案new_time的list变量,会添加保存每辆车的不堵塞不限速时跑完全程的理想最快时间（注意不是准确的完成时间），
    所以启动时间间隔以new_time[-1]为标准，批启动车辆数要2000以上才有得拼。
    之所以觉得B方案好一点，是因为同一时间启动车辆数越大死锁可能性越大，测试的时候能感觉出来，
    但后来才发现批启动车辆的数目也应与地图的规模有关，但目前只有4张大地图，而且12差不多，34差不多，很难摸索出来，当前对应比例有待考验
    只能比赛有多一张就摸索一次
    
    假设间隔时间为t，启动车辆为go_sum,总车辆数为car_sum,最后一批启动时间为(car_sum/go_sum -1) * t, 其实比值 t/go_sum 越小越好，
    如果考虑地图规模目前影响批启动车辆数的因素有(上面有，根据两种地图类型来初步调)
    1.地图全程总长度total_len
    2.地图总道数total_channal
    3.地图总路口数total_cross
    间隔扩大比例为 ratio = a*total_len + b*total_channal + c*total_cross (a,b,c是超参量)
    批启动车辆数 = 时间间隔 * ratio
    
    
    初赛最后一天补充：
    我们采用B方案 
    定值形式是：默认间隔为35  批启动数量为2100  成绩为 2380
    综合1,2,3,4 和比赛两张地图后我们的间隔扩大比例为
    ratio = (total_len**(1/3)/30 + total_channal/25 + total_cross/25) *1.0 （本地跑）2421
    但为了更好的名次 =_=  我们在比赛最后的时间选择细致的调参
    
    '''
    
    '''
    以下是处理和调用细节，为节省时间，边处理边写文件
    '''
    
    file = open(answer_path,'w') 
    file.write("#(carId,StartTime,RoadId...)" +'\n')
               
               
    cur_time = car_list[0][4]
    lay_time = 33 #默认35
    max_sum = 0 
    cur_car = 0
    #(total_len/3000 + total_channal/25 +total_cross/20 )*1.0
    #ratio = (total_len**(1/3)/30 + total_channal/25 + total_cross/25) *1.0
    limit_car = 1980 #默认2100
    #ilimit_car = int(lay_time * ratio)
    
    
    #max_spend_time = 0
    new_time = []
    now_length = 0
    
    for car in car_list:
       
        now_length = 0
        
        car_no = car[0]
        car_path = []
        #car_info = carStatus_dict[car_no]
        path = findBestPath(car_no,carStatus_dict,cross_dict,index_dict,max_sum)
        for i in range(1,len(path)):
            #print(cross_dict[path[i]])
            now_id = index_dict[path[i-1]]
            next_id = index_dict[path[i]]
            for cross_h in cross_dict[now_id]:
                if cross_h[0] ==  next_id:
                    #print(cross_h)
                    road_id = cross_h[1]
                    cross_h[3] += 1
                    now_length += cross_h[2]
                    cross_h[6] += (1/cross_h[4])
                    max_sum = max_sum if max_sum > cross_h[6] else cross_h[6]
            car_path.append(road_id)
            
        car_go = cur_time if cur_time > car[4] else car[4]
            
        res_str = "(" + str(car[0]) + "," + str(car_go) + "," + str(car_path)[1:-1] + ")"
        print(res_str)
        file.write(res_str +'\n')
            
        cur_car+=1
        new_time.append(car_go+ int(now_length/car[3]))
        #max_spend_time =  max_spend_time if max_spend_time > new_time else new_time
        
        if cur_car == limit_car:
            reset(cross_dict)
            cur_car = 0
            new_time = sorted(new_time)
            #print("new_time:"+ str(new_time))
            cur_time += lay_time
            new_time = []
            max_sum = 0
        
        
        
            
    
    
    file.close()   
    #print("保存文件成功")



if __name__ == "__main__":
    main()