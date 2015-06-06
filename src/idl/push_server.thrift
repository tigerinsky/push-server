namespace cpp tis
namespace php push
namespace py  push

enum LandingType { //跳转落地页类型
    INDEX=1, //app首页
    WAP=2, //某个指定的wap页面, 需要给出wap url
    COMMUNITY_DETAIL=3, //贴子详情页, 需要给出贴子tid
    FRIEND=4, //新的好友列表页
    PRIVATE_MSG=5,//私信详情页，需要给出私信的发起人的uid
    SYSTEM_MSG=6, //跳转到系统通知列表页
    USER=7, //跳转到个人主页，需要给出该人的uid
}

enum MessageType { //消息类型
    NOTIFY= 1,//通知
    NOTIFYRED = 2,//系统通知小红点
    EMAILRED = 3, //私信小红点
}

enum DeviceType {
    ANDROID=1,
    IOS=2,
}

struct Notify {
    1: required MessageType mtype;
    2: required LandingType ltype = 1;//mtype=1时有用
    3: required string content = '';//推送内容，mtype=1时有用，其它时候为''
    4: required string title='';
    5: required string url='';
    6: required i64 tid=0;
    7: required i32 uid=0;
    8: required i32 num=-1;//小红点增加数字
}

struct SingleNotifyRequest {
    1: required Notify notify;
    2: required i32 device_type;
    3: required string device_id;
}

struct BatchNotifyRequest {
    1: required list<string> device_id_list;
    2: required Notify notify;
    3: required i32 device_type;
    4: required i32 push_task_id=0;
    5: required i32 send_time=1426897707;
}

struct BroadcastRequest {
    1: required Notify notify;
    2: required i32 send_time=1426897707;
    3: required i32 push_task_id=0;
    4: required i32 device_type = 0;//0是给全部平台，1是android，2是ios
}

struct TagRequest {
    1: required i32 uid=0;//用户id
    2: required string xg_device_token='';
    3: required i32 op; //op=1:增加tag, op=2:删除tag
    4: required list<string> tag_list; //需要增加或者删除的tag 列表
}

/*struct PushTagsRequest {
    1: required list<string> tag_list;
    2: required Notify notify;
    3: required string tagsOp="AND";
}*/
struct ConditionPushRequest {
    1: required Notify notify;
    2: required i32 device_type=0;//0是全部，1是android，2是ios
    3: required string city;//城市名称，用逗号分隔，如果是全部城市，请只传字符串"all_city"
    4: required string school;//学校名称，用逗号分隔，如果是全部学校，请只传字符串"all_school"
    5: required string ukind_verify;//取两个值: verify, unverify
    6: required i32 send_time=1426897707;
    7: required i32 push_task_id = 0;
}

service PushService {
    string ping(),
    i32 single_notify(1:SingleNotifyRequest request),
    i32 batch_notify(1:BatchNotifyRequest request),
    i32 broadcast(1:BroadcastRequest request),
    i32 optag(1:TagRequest request),
    void condition_push(1:ConditionPushRequest request),
    //i32 push_tags(1:PushTagsRequest request)
    //void multicast(1:Notify notify, 2:i32 gid, 3:i32 begin_time, 4:i32 end_time) throws (1:InvalidParamException e),
}
